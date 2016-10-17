import numpy
from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp


# Primitives that aren't built in
# Turns out we don't really need safe versions IMO, raising the error
# allows the whole bad function to be chucked out.
#def protectedDiv(left, right):
#    with numpy.errstate(divide='ignore',invalid='ignore'):
#        x = numpy.divide(left, right)
#        if isinstance(x, numpy.ndarray):
#            x[numpy.isinf(x)] = 1
#            x[numpy.isnan(x)] = 1
#        elif numpy.isinf(x) or numpy.isnan(x):
#            raise ZeroDivisionError()
#    return x

#TODO: Users should be able to add their own, but I haven't decided on how to do that yet
def primitiveFactory(primitives, pset):
    for primitiveName in primitives:

        if primitiveName.lower() == "add":
            pset.addPrimitive(numpy.add, 2, name="add")
        elif primitiveName.lower() == "sub":
            pset.addPrimitive(numpy.subtract, 2, name="sub")
        elif primitiveName.lower() == "mul":
            pset.addPrimitive(numpy.multiply, 2, name="mul")
        elif primitiveName.lower() == "div":
            pset.addPrimitive(numpy.true_divide, 2, name="div")
        elif primitiveName.lower() == "neg":
            pset.addPrimitive(numpy.negative, 1, name="neg")
        elif primitiveName.lower() == "power":
            pset.addPrimitive(numpy.power, 2, name="power")
        elif primitiveName.lower() == "abs":
            pset.addPrimitive(numpy.absolute, 1, name="abs")
        elif primitiveName.lower() == "exp":
            pset.addPrimitive(numpy.exp, 1, name="exp")
        elif primitiveName.lower() == "exp2":
            pset.addPrimitive(numpy.exp2, 1, name="exp2")
        elif primitiveName.lower() == "log":
            pset.addPrimitive(numpy.log, 1, name="log")
        elif primitiveName.lower() == "log2":
            pset.addPrimitive(numpy.log2, 1, name="log2")
        elif primitiveName.lower() == "log10":
            pset.addPrimitive(numpy.log10, 1, name="log10")
        elif primitiveName.lower() == "sqrt":
            pset.addPrimitive(numpy.sqrt, 1, name="sqrt")
        elif primitiveName.lower() == "square":
            pset.addPrimitive(numpy.square, 1, name="square")
        elif primitiveName.lower() == "reciprocal":
            pset.addPrimitive(numpy.reciprocal, 1, name="reciprocal")

        elif primitiveName.lower() == "sin":
            pset.addPrimitive(numpy.sin, 1, name="sin")
        elif primitiveName.lower() == "cos":
            pset.addPrimitive(numpy.cos, 1, name="cos")
        elif primitiveName.lower() == "tan":
            pset.addPrimitive(numpy.tan, 1, name="tan")
        elif primitiveName.lower() == "arcsin":
            pset.addPrimitive(numpy.arcsin, 1, name="asin")
        elif primitiveName.lower() == "arccos":
            pset.addPrimitive(numpy.arccos, 1, name="acos")
        elif primitiveName.lower() == "arctan":
            pset.addPrimitive(numpy.arctan, 1, name="atan")
        elif primitiveName.lower() == "arctan2":
            pset.addPrimitive(numpy.arctan2, 2, name="atan2")
        elif primitiveName.lower() == "sinh":
            pset.addPrimitive(numpy.sinh, 1, name="sinh")
        elif primitiveName.lower() == "cosh":
            pset.addPrimitive(numpy.cosh, 1, name="cosh")
        elif primitiveName.lower() == "tanh":
            pset.addPrimitive(numpy.tanh, 1, name="tanh")
        elif primitiveName.lower() == "arcsinh":
            pset.addPrimitive(numpy.arcsinh, 1, name="asinh")
        elif primitiveName.lower() == "arccosh":
            pset.addPrimitive(numpy.arccosh, 1, name="acosh")
        elif primitiveName.lower() == "arctanh":
            pset.addPrimitive(numpy.arctanh, 1, name="atanh")
        else:
            print "WARNING: Unknown primitive: ", primitiveName
    
