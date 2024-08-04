def simple_forward(arg):
    a = 5
    a = 7
    LABEL .done
    assert a == 5
    print(F"WE HAVE WON: {a}")

simple_forward(1)
# a = 3
GOTO .done