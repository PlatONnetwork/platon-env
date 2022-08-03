from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from functools import wraps

error_msg = '{} {} do {} failed:{}'


def executor_wrapper(obj, func_name):
    """ 在try中执行方法，当报错时返回错误信息

    Args:
        obj: 需要执行方法的节点列表
        func_name (str): 需要执行的方法名
    """
    func = obj.__getattribute__(func_name)

    @wraps(func)
    def wrap_func(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            return False, error_msg.format(type(obj), obj, func.__name__, e.with_traceback())
        # todo: 正常返回时，增加对应的obj信息
        return True, result

    return wrap_func


def concurrent_executor(objects, func_name, *args, **kwargs):
    """ 使用线程池并行执行方法

    Args:
        objects: 需要执行方法的对象列表
        func_name (str): 需要执行的方法名
        args: 方法参数
        kwargs: 关键字参数
    Returns:
        succeed: 正常执行成功后的返回信息
    """
    succeed, failed = [], []
    with ThreadPoolExecutor(max_workers=20) as thread_pool:
        runs = []
        for obj in objects:
            func = executor_wrapper(obj, func_name)
            runs.append(thread_pool.submit(func, *args, **kwargs))
        done, undone = wait(runs, timeout=30, return_when=ALL_COMPLETED)
    for piece in done:
        is_succeed, result = piece.result()
        succeed.append(result) if is_succeed else failed.append(result)
    if failed:
        raise Exception(f'executor {func.__name__} failed: {failed}')
    # todo: 增加对undone的处理
    return succeed
