def errors(f):
    def errorWrapper(*args, **kwargs):
        if globalmachinekit_running == False:
            return jsonify({"errors": errorMessages[0]}), 500

        return f(*args, **kwargs)
    errorWrapper.__name__ = f.__name__
    return errorWrapper
