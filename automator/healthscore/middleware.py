import logging
import traceback


class ExceptionMiddleware(object):

    def __init__(self, get_response):
        self.log = logging.getLogger('requested')
        self.get_response = get_response

    def process_exception(self, request, exception):
        self.log.exception(traceback.format_exc().replace('\n', ' '), extra={'user': request.user.username})

    def __call__(self, request):
        response = self.get_response(request)
        return response
