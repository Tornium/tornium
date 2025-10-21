# Adapted from https://blog.alex.balgavy.eu/creating-a-timeout-decorator-in-python/

import functools
import multiprocessing
import typing

# Same as before
TimeoutReturnType = typing.Union[int, typing.Any]

# Stores the original, undecorated functions
_original_functions = {}


# Given a function name, runs the corresponding undecorated function
def _timeout_func_runner(name: str, *args, **kwargs) -> typing.Any:
    return _original_functions[name](*args, **kwargs)


# Mostly the same as before...
def timeout(
    n: float,
) -> typing.Callable[[typing.Callable[..., TimeoutReturnType]], typing.Callable[..., TimeoutReturnType]]:
    def decorate(
        nonterminating_func: typing.Callable[..., TimeoutReturnType]
    ) -> typing.Callable[..., TimeoutReturnType]:
        # ...except for this: store the original function, using its name as a key
        _original_functions[nonterminating_func.__name__] = nonterminating_func

        @functools.wraps(nonterminating_func)
        def wrapper(*args, **kwargs) -> TimeoutReturnType:
            rcv, snd = multiprocessing.Pipe()

            # ...and this: instead of calling the nonterminating function directly,
            # call it via the dictionary.
            proc = multiprocessing.Process(
                target=_timeout_func_runner,
                args=(
                    nonterminating_func.__name__,
                    *args,
                ),
                kwargs={"snd": snd, **kwargs},
            )
            proc.start()

            proc.join(timeout=n)

            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=10)
                if proc.is_alive():
                    proc.kill()
                    proc.join()

            assert proc.exitcode is not None, "process should be terminated at this point"

            if proc.exitcode == 0:
                result = rcv.recv()
                rcv.close()
                return result
            else:
                raise TimeoutError(f"Wrapped function timed out with code {proc.exitcode}")

        return wrapper

    return decorate
