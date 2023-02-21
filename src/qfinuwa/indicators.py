
from functools import wraps
import inspect
from itertools import product
from collections import defaultdict
import numpy as np

class Indicators:

    def __init__(self, stockdata):

        self.params = self.defaults
        # self._stockdata = stockdata
        self._data = stockdata._stock_df
        self._L = len(stockdata)
        # self._L = 3

        self._cache = dict()
        self._funcn_to_indicator_map = dict()
        # for func_name, func in self._indicator_functions.items():
        self.add_parameters(self.params)

    
    #----[ Properties ]--------------------------------------------------------
    @property
    def indicators(self):
        return sorted(sum((v for v in self._funcn_to_indicator_map.values()), start = []))

    @property
    def indicator_groups(self):
        return sorted(list(self._funcn_to_indicator_map.keys()))

    @property
    def _indicator_functions(self):
        # TODO: filter by only functions
        cls = type(self)

        return {k: v for k, v in inspect.getmembers(cls)
                if callable(v) and hasattr(getattr(cls, k), 'Indicator') and not k.startswith('__')}

    @property
    def defaults(self):
        
        def get_defaults(func): 
            signature = inspect.signature(func)
            return {
                k: v.default
                for k, v in signature.parameters.items()
                if v.default is not inspect.Parameter.empty
            }
        return {name: get_defaults(function) for name, function in self._indicator_functions.items()}

    @property
    def _stocks(self):
        return list(self._data.keys())

    @classmethod
    def Indicator(cls, func):
        @wraps(func)
        def wrapper_func(*_args, **_kwargs):
            return func(*_args, **_kwargs)
        wrapper_func.Indicator = True
        return wrapper_func

    # ----[/Properties]--------------------------------------------------------

    def _fill_in_params(self, params):
        curr_params = {k: {k1:v1 for k1, v1 in v.items()} for k,v in self.params.items()}
        for indicator in params:   
            curr_params[indicator].update(params[indicator])
        return curr_params

    def update_parameters(self, params):

        self._raise_invalid_params(params)
            
        self.params = self._fill_in_params(params)
        
        self.add_parameters(self.params)
    
    def _raise_invalid_params(self, params):
        defaults = self.defaults

        if params.keys() - defaults.keys():
            raise ValueError(f'Indicator group(s) not found: {params.keys() - defaults.keys()}')

        for func_name, f_params in params.items():
            if f_params.keys() - defaults[func_name].keys():
                raise ValueError(f'Indicator(s) not found in {func_name}: {f_params.keys() - defaults[func_name].keys()}')

    def add_parameters(self, params):

        self._raise_invalid_params(params)

        for func_name, f_params in params.items():
            if func_name not in self._indicator_functions:
                raise ValueError(f'Indicator function {func_name} not found')

            self._add_indicator(func_name, self._indicator_functions[func_name], f_params) 


    def _add_indicator(self, func_name, func, params = None):
        
        if params is None:
            params = self.defaults[func_name]

        if self._is_cached(func_name, params):
            return
        
        to_cache = dict()
        for stock, data in self._data.items():

            out = func(self, data, **params)
            if not isinstance(out, dict):
                raise ValueError(f'Indicator function {func_name} must return a dict')

            self._funcn_to_indicator_map[func_name] = sorted(list(out.keys()))
    
            # for indicator, value in out.items():
            for indicator, value in out.items():
                if indicator not in to_cache:
                    to_cache[indicator] = dict()
                to_cache[indicator].update({stock: value}) 

        self._cache_indicator(func_name, params, to_cache)

    
    #---------[CACHE]---------#
    def _hashable(self, function_name, params):
        return (function_name, tuple(sorted(params.items())))

    def _cache_indicator(self, function_name, params, stock_values):
        key = self._hashable(function_name, params)
        self._cache[key] = stock_values
        return

    def _is_cached(self, function_name, params):
        return self._hashable(function_name, params) in self._cache

    def _get_cached(self, function_name, params, indicator):

        if not self._is_cached(function_name, params):
            return None
        
        key = self._hashable(function_name, params)
        return self._cache[key][indicator]

    #---------[/CACHE]---------#       


    def get_permutations(self, funcn_to_params):

        self._raise_invalid_params(funcn_to_params)
        
        funcn_to_params = self._fill_in_params(funcn_to_params)


        combinations = defaultdict(list)

        # with tqdm(total=len_indicator_comb, desc="Precomputing indicator variants.") as bar:
        for indicator, paramters in funcn_to_params.items():
            
            param, val = zip(*paramters.items())

            val = map(lambda v: v if isinstance(v, list) else [v], val)

            permutations_dicts = [dict(zip(param, v))
                            for v in product(*val)]

            for perm in permutations_dicts:                
                self._add_indicator(indicator, self._indicator_functions[indicator], perm)
                combinations[indicator].append(perm)
                # bar.update(1)

        # get every combination of different indicators
        every_combination =  [dict(zip(combinations.keys(), c)) for c in product(*combinations.values())]

        return every_combination

    def iterate_params(self, params=None):

        if params is None:
            params = self.defaults

        params = self._fill_in_params(params)
        self.add_parameters(params)

        # params maps function name to parameters

        self._indicators_iterations = {indicator: np.array(list(self._get_cached(funcn, params[funcn], indicator).values())) for funcn, indicators in self._funcn_to_indicator_map.items() for indicator in indicators}
       
        return self.__iter__()
    
    def __iter__(self):
        self._iterate_indicators = {stock: {indicator: None for indicator in self.indicators} for stock in self._stocks}
        self._indexes = list(product(range(len(self._stocks)), self.indicators))
        self._i = 1
        return self

    def __next__(self):
        if self._i > len(self):
            self._indicators_iterations = None
            self._iterate_indicators = None
            self._indexes = None
            self._i = None
            raise StopIteration(f'Index {self._i } out of range.')

        for s, indicator in self._indexes: 
            self._iterate_indicators[self._stocks[s]][indicator] = self._indicators_iterations[indicator][s, :self._i]

        self._i += 1
        return self._iterate_indicators

    def __len__(self):
        return self._L