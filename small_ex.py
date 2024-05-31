from functools import wraps, partial
import dill
import datetime


def small_capture_example(func=None, logger=None):
    if func is None:
        return partial(small_capture_example, logger=logger)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f'Capturing function {func.__name__} with args {args} and kwargs {kwargs}')
        with open(f'{func.__name__}_args.dill', 'wb') as file:
            file.write(dill.dumps(args[1:]))
        with open(f'{func.__name__}_kwargs.dill', 'wb') as file:
            file.write(dill.dumps(kwargs))

        return func(*args, **kwargs)

    return wrapper


class Turtle:
    

    @small_capture_example
    def a_function(self, today, num_days, param_3=None):
        print(f'Today is {datetime.datetime.strftime(today, '%Y-%m-%d')} and num_days is {num_days} and param_3 is {param_3}')




if __name__ == '__main__':
    t = Turtle()
    t.a_function(datetime.datetime(2024, 5, 23), 3, param_3='test')

    with open('a_function_args.dill', 'rb') as file:
        args = dill.loads(file.read())
    with open('a_function_kwargs.dill', 'rb') as file:
        kwargs = dill.loads(file.read())

    print(f'Loaded args: {args}')
    t.a_function(*args, **kwargs)