import numpy as np

from ..module import Module

CLASS_NAME = 'DenseTimes'


class DenseTimes(Module):
    """Structure to store transient data.
    """

    N_TIMES = 100

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._n_times = kwargs[
            'n_times'] if 'n_times' in kwargs else self.N_TIMES

    def process(self, **kwargs):
        self._times = kwargs['times']
        self._t_explosion = kwargs['texplosion']

        outputs = {}
        outputs['densetimes'] = kwargs['times']
        max_times = max(kwargs['times'])
        if max_times > kwargs['texplosion']:
            outputs['densetimes'] = sorted([
                x + self._t_explosion
                for x in list(
                    np.linspace(
                        0.0, max_times - self._t_explosion, num=self._n_times))
            ] + self._times)
        return outputs