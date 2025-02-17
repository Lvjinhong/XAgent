import os
import glob
import yaml
import json5 as json

from typing import Optional, Tuple
from tenacity import retry, stop_after_attempt,retry_if_not_exception_type
from colorama import Fore
from openai.error import AuthenticationError, PermissionError, InvalidRequestError
from .request import openai_chatcompletion_request
from XAgent.config import CONFIG
from XAgent.loggers.logs import logger

class FunctionManager:
    def __init__(self,
                 function_cfg_dir=os.path.join(os.path.dirname(__file__),'functions'),
                 pure_function_cfg_dir=os.path.join(os.path.dirname(__file__),'pure_functions'),):
        self.function_cfg_dir = function_cfg_dir
        self.pure_function_cfg_dir = pure_function_cfg_dir
        self.default_completion_kwargs = CONFIG.default_completion_kwargs
        self.function_cfgs = {}
        
        for cfg_file in glob.glob(os.path.join(self.function_cfg_dir,'*.yaml')) + glob.glob(os.path.join(self.function_cfg_dir,'*.yml')):
            with open(cfg_file,'r') as f:
                function_cfg = yaml.load(f,Loader=yaml.FullLoader)
            self.function_cfgs[function_cfg['function']['name']] = function_cfg

        for cfg_file in glob.glob(os.path.join(self.pure_function_cfg_dir,'*.yaml')) + glob.glob(os.path.join(self.pure_function_cfg_dir,'*.yml')):
            with open(cfg_file,'r') as f:
                function_cfg = yaml.load(f,Loader=yaml.FullLoader)
            for function in function_cfg['functions']:
                self.function_cfgs[function['name']] = function
    
    def get_function_schema(self,function_name:str)->dict|None:
        return self.function_cfgs.get(function_name,None)
    
    def register_function(self,function_schema:dict):
        if function_schema['name'] in self.function_cfgs:
            return
        self.function_cfgs[function_schema['name']] = function_schema
        
    @retry(retry=retry_if_not_exception_type((AuthenticationError, PermissionError, InvalidRequestError)),stop=stop_after_attempt(CONFIG.max_retry_times),reraise=True)
    def execute(self,function_name:str,return_generation_usage:bool=False,function_cfg:dict=None,**kwargs,)->Tuple[dict,Optional[dict]]:
        if function_cfg is None and function_name in self.function_cfgs:
            function_cfg = self.function_cfgs.get(function_name)
        else:
            raise KeyError(f'Configure for function {function_name} not found.')
        
        completions_kwargs:dict = function_cfg.get('completions_kwargs',self.default_completion_kwargs)
        # print(function_cfg['function_prompt'],kwargs)
        function_prompt = str(function_cfg['function_prompt'])
        # print(kwargs)
        function_prompt = function_prompt.format(**kwargs)
        # print(function_prompt)
        messages = [{'role':'user','content':function_prompt}]
        functions = [function_cfg['function']]
        function_call = {'name':function_cfg['function']['name']}
        logger.typewriter_log(f'Executing AI Function: {function_name}', Fore.YELLOW)
        response = openai_chatcompletion_request(
            messages=messages,
            functions=functions,
            function_call=function_call,
            function_call_check=True,
            **completions_kwargs
        )
        returns = json.loads(response['choices'][0]['message']['function_call']['arguments'])
        
        if return_generation_usage:
            return returns, response['usage']
        return returns
    
    def __getitem__(self,function_name,return_generation_usage=False,**kwargs):
        return self.execute(function_name,return_generation_usage,**kwargs)
    def __call__(self, function_name,return_generation_usage=False,**kwargs):
        return self.execute(function_name,return_generation_usage,**kwargs)

function_manager = FunctionManager()