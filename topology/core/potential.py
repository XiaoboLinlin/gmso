import warnings
import sympy
import unyt as u


class Potential(object):
    """An abstract potential class.

    Potential stores a general interaction between components of a chemical
    topology that can be specified by a mathematical expression. The functional
    form of the potential is stored as a `sympy` expression and the parameters
    are stored explicitly. This class is agnostic to the instantiation of the
    potential, which can be e.g. a non-bonded potential, a bonded potential, an
    angle potential, a dihedral potential, etc. and is designed to be inherited
    by classes that represent these potentials.

    Parameters
    ----------
    name : str, default="Potential" 
        The name of the potential.
    expression : str or sympy.Expr, default='a*x+b'
        The mathematical expression describing the functional form of the 
        potential. 
    parameters : dict of str : unyt.unyt_quantity pairs,
        default={'a': 1.0*u.dimensionless, 'b': 1.0*u.dimensionless}
        The parameters of the potential and their values, as unyt quantities.
    independent_variables : str or sympy.Symbol or list or set thereof
        The independent variables in the expression of the potential.

    """

    def __init__(self,
                 name="Potential",
                 expression='a*x+b',
                 parameters={
                     'a': 1.0*u.dimensionless,
                     'b': 1.0*u.dimensionless},
                 independent_variables={'x'},
                 ):

        self._name = name
        self._parameters = _validate_parameters(parameters)
        self._independent_variables = _validate_independent_variables(independent_variables)
        self._expression = _validate_expression(expression)

        self._validate_expression_parameters()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        self._name = val

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def parameters(self, newparams):
        newparams = _validate_parameters(newparams)

        self._parameters.update(newparams)
        self._validate_expression_parameters()

    @property
    def independent_variables(self):
        return self._independent_variables

    @independent_variables.setter
    def independent_variables(self, indep_vars):
        self._independent_variables = _validate_independent_variables(indep_vars)

    @property
    def expression(self):
        return self._expression

    @expression.setter
    def expression(self, expression):
        self._expression = _validate_expression(expression)

        self._validate_expression_parameters()

    def set_expression(self, expression=None, parameters=None, independent_variables=None):
        """Set the expression, parameters, and independent variables for this potential.

        Parameters
        ----------
        expression: sympy.Expression or string
            The mathematical expression corresponding to the potential
            If None, the expression remains unchanged
        parameters: dict
            {parameter: value} in the expression
            If None, the parameters remain unchanged

        Notes
        -----
        Be aware of the symbols used in the `expression` and `parameters`.
        If unnecessary parameters are supplied, an error is thrown.
        If only a subset of the parameters are supplied, they are updated
            while the non-passed parameters default to the existing values
       """
        if expression is not None:
            self._expression = _validate_expression(expression)

        if parameters is None:
            parameters = self._parameters
        else:
            parameters = _validate_parameters(parameters)
            if not set(self._parameters).intersection(set(parameters)):
                if expression is None:
                    raise ValueError('`parameters` argument includes no '
                                     'variables found in expression. Expected '
                                     'at least one of {}'.format(
                                        self._parameters.keys()))
            self._parameters.update(parameters)

        if independent_variables is not None:
            self._independent_variables = _validate_independent_variables(independent_variables)

        if not set(parameters.keys()).isdisjoint(self._expression.free_symbols):
            raise ValueError('Mismatch between parameters and expression symbols')

        self._validate_expression_parameters()

    def _validate_expression_parameters(self):
        # Check for unused symbols
        parameter_symbols = sympy.symbols(set(self._parameters.keys()))
        independent_variable_symbols = self._independent_variables
        used_symbols = parameter_symbols.union(independent_variable_symbols)
        unused_symbols = self.expression.free_symbols - used_symbols
        if len(unused_symbols) > 0:
            warnings.warn('You supplied parameters with '
                          'unused symbols {}'.format(unused_symbols))

        if used_symbols != self.expression.free_symbols:
            symbols = sympy.symbols(set(self.parameters.keys()))
            if symbols != self.expression.free_symbols:
                missing_syms = self.expression.free_symbols - symbols - self._independent_variables
                if missing_syms:
                    raise ValueError("Missing necessary parameters to evaluate "
                                     "NB expression. Missing symbols: {}"
                                     "".format(missing_syms))
                extra_syms = symbols ^ self.expression.free_symbols
                warnings.warn("NB expression and parameter"
                              " symbols do not agree,"
                              " extraneous symbols:"
                              " {}".format(extra_syms))

    def __eq__(self, other):
        name_match = (self.name == other.name)
        parameter_match = (self.parameters == other.parameters)
        expression_match = (self.expression == other.expression)

        return all([
            name_match, parameter_match,
            expression_match
        ])

    def __repr__(self):
        desc = "<Potential {}, id {}>".format(self._name, id(self))
        return desc


def _validate_parameters(parameters):
    if not isinstance(parameters, dict):
        raise ValueError("Please enter dictionary for parameters")
    for key, val in parameters.items():
        if not isinstance(val, u.unyt_array):
            raise ValueError('Parameter value {} lacks a unyt'.format(val))
        if not isinstance(key, str):
            raise ValueError('Parameter key {} is not a str'.format(key))

    return parameters


def _validate_independent_variables(indep_vars):
    if isinstance(indep_vars, str):
        indep_vars = {sympy.symbols(indep_vars)}
    elif isinstance(indep_vars, sympy.symbol.Symbol):
        indep_vars = {indep_vars}
    elif isinstance(indep_vars, (list, set)):
        if all([isinstance(val, sympy.symbol.Symbol) for val in indep_vars]):
            pass
        elif all([isinstance(val, str) for val in indep_vars]):
            indep_vars = set([sympy.symbols(val) for val in indep_vars])
        else:
            raise ValueError('`independent_variables` argument was a list '
                             'or set of mixed variables. Please enter a '
                             'list or set of either only strings or only '
                             'sympy symbols')
    else:
        raise ValueError("Please enter a string, sympy expression, "
                         "or list or set thereof for independent_variables")

    return indep_vars


def _validate_expression(expression):
    if expression is None or isinstance(expression, sympy.Expr):
        pass
    elif isinstance(expression, str):
        expression = sympy.sympify(expression)
    else:
        raise ValueError("Please enter a string, sympy expression, "
                         "or None for expression")

    return expression
