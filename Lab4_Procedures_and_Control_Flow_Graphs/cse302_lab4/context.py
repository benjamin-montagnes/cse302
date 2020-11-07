class Context:
    """Symbol management"""
    # def _make_builtins():
    #     cx = dict()
    #     ty=FUNC(INT, INT, INT)
    #     for op in ('+', '-', '*', '/', '%', '&', '|', '^', '<<', '>>'):
    #         cx[op] = ty
    #     ty = FUNC(INT, INT)
    #     for op in ('u-', '~'):
    #         cx[op] = ty
    #     ty = FUNC(BOOL, INT, INT)
    #     for op in ('==', "!=", '<', '<=', '>', '>='):
    #         cx[op] = ty
    #     ty = FUNC(BOOL, BOOL, BOOL)
    #     for op in ('&&', '||'):
    #         cx[op] = ty
    #     cx['!'] = FUNC(BOOL, BOOL)
    #     cx['__bx_print_int'] = FUNC(VOID, INT)
    #     cx['__bx_print_bool'] = FUNC(VOID, BOOL)
    #     return cx
    # _builtins = _make_builtins()

    def __init__(self):
        # self.global_defs = self._builtins.copy()
        self.local_defs = [{}]

    @property
    def current(self):
        """Return the current scope"""
        # if len(self.local_defs) == 0:
        #     return self.global_defs
        # else:
        return self.local_defs[-1]
    
    @property
    def first_scope(self):
        return self.local_defs[0]

    def enter(self):
        """enter a new (local) scope"""
        self.local_defs.append({})

    def leave(self):
        """leave a local scope"""
        self.local_defs.pop()

    def _contains_(self):
        return len(self.local_defs) == 1

    def _getitem_(self, name):
        """Lookup the name in the context."""
        for i in range(len(self.local_defs)-1, -1, -1):
            if name in self.local_defs[i]: return self.local_defs[i][name]
        return None
    
    def _str_(self, scope):
        for symbol in scope:
            print("{}\t{}".format(symbol, scope[symbol]))

context = Context()
