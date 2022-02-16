from datetime import date

from django.db import models
from picklefield import PickledObjectField

S1 = 'Hello World'
T1 = (1, 2, 3, 4, 5)
L1 = [1, 2, 3, 4, 5]
D1 = {1: 1, 2: 4, 3: 6, 4: 8, 5: 10}
D2 = {1: 2, 2: 4, 3: 6, 4: 8, 5: 10}


class FakeCopyDataType(str):
    def __deepcopy__(self, memo):
        raise ValueError('Please dont copy me')


class FakeCustomDataType(str):
    pass


class FakeModel(models.Model):
    pickle_field = PickledObjectField()
    compressed_pickle_field = PickledObjectField(compress=True)
    default_pickle_field = PickledObjectField(default=(D1, S1, T1, L1))
    callable_pickle_field = PickledObjectField(default=date.today)
    non_copying_field = PickledObjectField(copy=False, default=FakeCopyDataType('boom!'))
    nullable_pickle_field = PickledObjectField(null=True)


class MinimalTestingModel(models.Model):
    pickle_field = PickledObjectField()
