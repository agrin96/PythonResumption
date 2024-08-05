import time

check = 0
def simple_forward(arg):
    a = 5

    if arg == 1:
        print("Ready to Interrupt")
        time.sleep(3.0)
        print("Resumed")
    
    assert a == 5
    print(F"Python Heresy successfully committed: {a}")
    global check
    check = 1

print("Starting 'Nothing to see here''")
while check == 0:
    simple_forward(1)

print("May Guido Forgive me")
