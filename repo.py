from dagster import op


@op
def hello():
    return 1


@op
def goodbye(foo):
    if foo != 1:
        raise Exception("Bad io manager")
    return foo * 2


