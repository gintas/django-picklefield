import json
from datetime import date
from unittest.mock import patch

from django.core import checks, serializers
from django.db import IntegrityError, models
from django.test import SimpleTestCase, TestCase
from django.test.utils import isolate_apps

from picklefield.fields import (
    PickledObjectField, dbsafe_encode, wrap_conflictual_object,
)

from .models import (
    D1, D2, L1, S1, T1, MinimalTestingModel, TestCopyDataType,
    TestCustomDataType, TestingModel,
)


class PickledObjectFieldTests(TestCase):
    def setUp(self):
        self.testing_data = (D2, S1, T1, L1,
                             TestCustomDataType(S1),
                             MinimalTestingModel)
        return super().setUp()

    def test_data_integrity(self):
        """
        Tests that data remains the same when saved to and fetched from
        the database, whether compression is enabled or not.
        """
        for value in self.testing_data:
            model_test = TestingModel(pickle_field=value, compressed_pickle_field=value)
            model_test.save()
            model_test = TestingModel.objects.get(id__exact=model_test.id)
            # Make sure that both the compressed and uncompressed fields return
            # the same data, even thought it's stored differently in the DB.
            self.assertEqual(value, model_test.pickle_field)
            self.assertEqual(value, model_test.compressed_pickle_field)
            self.assertIsNone(model_test.nullable_pickle_field)
            # Make sure we can also retrieve the model
            model_test.save()
            model_test.delete()

        # Make sure the default value for default_pickled_field gets stored
        # correctly and that it isn't converted to a string.
        model_test = TestingModel(pickle_field=1, compressed_pickle_field=1)
        model_test.save()
        model_test = TestingModel.objects.get(id__exact=model_test.id)
        self.assertEqual((D1, S1, T1, L1), model_test.default_pickle_field)
        self.assertEqual(date.today(), model_test.callable_pickle_field)

    def test_lookups(self):
        """
        Tests that lookups can be performed on data once stored in the
        database, whether compression is enabled or not.

        One problem with cPickle is that it will sometimes output
        different streams for the same object, depending on how they are
        referenced. It should be noted though, that this does not happen
        for every object, but usually only with more complex ones.

        >>> from pickle import dumps
        >>> t = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, \
        ... 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        >>> dumps(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, \
        ... 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]))
        "((dp0\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np1\n(I1\nI2\nI3\nI4\nI5\ntp2\n(lp3\nI1\naI2\naI3\naI4\naI5\natp4\n."
        >>> dumps(t)
        "((dp0\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np1\n(I1\nI2\nI3\nI4\nI5\ntp2\n(lp3\nI1\naI2\naI3\naI4\naI5\natp4\n."
        >>> # Both dumps() are the same using pickle.

        >>> from cPickle import dumps
        >>> t = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        >>> dumps(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np2\n(I1\nI2\nI3\nI4\nI5\ntp3\n(lp4\nI1\naI2\naI3\naI4\naI5\nat."
        >>> dumps(t)
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\n(I1\nI2\nI3\nI4\nI5\nt(lp2\nI1\naI2\naI3\naI4\naI5\natp3\n."
        >>> # But with cPickle the two dumps() are not the same!
        >>> # Both will generate the same object when loads() is called though.

        We can solve this by calling deepcopy() on the value before
        pickling it, as this copies everything to a brand new data
        structure.

        >>> from cPickle import dumps
        >>> from copy import deepcopy
        >>> t = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        >>> dumps(deepcopy(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np2\n(I1\nI2\nI3\nI4\nI5\ntp3\n(lp4\nI1\naI2\naI3\naI4\naI5\nat."
        >>> dumps(deepcopy(t))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np2\n(I1\nI2\nI3\nI4\nI5\ntp3\n(lp4\nI1\naI2\naI3\naI4\naI5\nat."
        >>> # Using deepcopy() beforehand means that now both dumps() are idential.
        >>> # It may not be necessary, but deepcopy() ensures that lookups will always work.

        Unfortunately calling copy() alone doesn't seem to fix the
        problem as it lies primarily with complex data types.

        >>> from cPickle import dumps
        >>> from copy import copy
        >>> t = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        >>> dumps(copy(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np2\n(I1\nI2\nI3\nI4\nI5\ntp3\n(lp4\nI1\naI2\naI3\naI4\naI5\nat."
        >>> dumps(copy(t))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\n(I1\nI2\nI3\nI4\nI5\nt(lp2\nI1\naI2\naI3\naI4\naI5\natp3\n."

        """  # noqa
        for value in self.testing_data:
            model_test = TestingModel(pickle_field=value, compressed_pickle_field=value)
            model_test.save()
            # Make sure that we can do an ``exact`` lookup by both the
            # pickle_field and the compressed_pickle_field.
            wrapped_value = wrap_conflictual_object(value)
            model_test = TestingModel.objects.get(pickle_field__exact=wrapped_value,
                                                  compressed_pickle_field__exact=wrapped_value)
            self.assertEqual(value, model_test.pickle_field)
            self.assertEqual(value, model_test.compressed_pickle_field)
            # Make sure that ``in`` lookups also work correctly.
            model_test = TestingModel.objects.get(pickle_field__in=[wrapped_value],
                                                  compressed_pickle_field__in=[wrapped_value])
            self.assertEqual(value, model_test.pickle_field)
            self.assertEqual(value, model_test.compressed_pickle_field)
            # Make sure that ``is_null`` lookups are working.
            self.assertEqual(1, TestingModel.objects.filter(pickle_field__isnull=False).count())
            self.assertEqual(0, TestingModel.objects.filter(pickle_field__isnull=True).count())
            model_test.delete()

        # Make sure that lookups of the same value work, even when referenced
        # differently. See the above docstring for more info on the issue.
        value = (D1, S1, T1, L1)
        model_test = TestingModel(pickle_field=value, compressed_pickle_field=value)
        model_test.save()
        # Test lookup using an assigned variable.
        model_test = TestingModel.objects.get(pickle_field__exact=value)
        self.assertEqual(value, model_test.pickle_field)
        # Test lookup using direct input of a matching value.
        model_test = TestingModel.objects.get(
            pickle_field__exact=(D1, S1, T1, L1),
            compressed_pickle_field__exact=(D1, S1, T1, L1),
        )
        self.assertEqual(value, model_test.pickle_field)
        model_test.delete()

    def test_limit_lookups_type(self):
        """
        Test that picklefield supports lookup type limit
        """
        with self.assertRaisesMessage(TypeError, 'Lookup type gte is not supported'):
            TestingModel.objects.filter(pickle_field__gte=1)

    def test_serialization(self):
        model = MinimalTestingModel(pk=1, pickle_field={'foo': 'bar'})
        serialized = serializers.serialize('json', [model])
        data = json.loads(serialized)

        # determine output at runtime, because pickle output in python 3
        # is different (but compatible with python 2)
        p = dbsafe_encode({'foo': 'bar'})

        self.assertEqual(data, [{
            'pk': 1,
            'model': 'tests.minimaltestingmodel',
            'fields': {"pickle_field": p}},
        ])

        for deserialized_test in serializers.deserialize('json', serialized):
            self.assertEqual(deserialized_test.object, model)

    def test_no_copy(self):
        TestingModel.objects.create(
            pickle_field='Copy Me',
            compressed_pickle_field='Copy Me',
            non_copying_field=TestCopyDataType('Dont Copy Me')
        )

        with self.assertRaises(ValueError):
            TestingModel.objects.create(
                pickle_field=TestCopyDataType('BOOM!'),
                compressed_pickle_field='Copy Me',
                non_copying_field='Dont copy me'
            )

    def test_empty_strings_not_allowed(self):
        with self.assertRaises(IntegrityError):
            MinimalTestingModel.objects.create()

    def test_decode_error(self):
        def mock_decode_error(*args, **kwargs):
            raise Exception()

        model = MinimalTestingModel.objects.create(pickle_field={'foo': 'bar'})
        model.save()

        self.assertEqual(
            {'foo': 'bar'}, MinimalTestingModel.objects.get(pk=model.pk).pickle_field
        )

        with patch('picklefield.fields.dbsafe_decode', mock_decode_error):
            encoded_value = dbsafe_encode({'foo': 'bar'})
            self.assertEqual(encoded_value, MinimalTestingModel.objects.get(pk=model.pk).pickle_field)


class PickledObjectFieldDeconstructTests(SimpleTestCase):
    def test_protocol(self):
        field = PickledObjectField()
        self.assertNotIn('protocol', field.deconstruct()[3])
        with self.settings(PICKLEFIELD_DEFAULT_PROTOCOL=3):
            field = PickledObjectField(protocol=4)
            self.assertEqual(field.deconstruct()[3].get('protocol'), 4)
            field = PickledObjectField(protocol=3)
            self.assertNotIn('protocol', field.deconstruct()[3])


@isolate_apps('tests')
class PickledObjectFieldCheckTests(SimpleTestCase):
    def test_mutable_default_check(self):
        class Model(models.Model):
            list_field = PickledObjectField(default=[])
            dict_field = PickledObjectField(default={})
            set_field = PickledObjectField(default=set())

        msg = (
            "PickledObjectField default should be a callable instead of a mutable instance so "
            "that it's not shared between all field instances."
        )

        self.assertEqual(Model().check(), [
            checks.Warning(
                msg=msg,
                hint='Use a callable instead, e.g., use `list` instead of `[]`.',
                obj=Model._meta.get_field('list_field'),
                id='picklefield.E001',
            ),
            checks.Warning(
                msg=msg,
                hint='Use a callable instead, e.g., use `dict` instead of `{}`.',
                obj=Model._meta.get_field('dict_field'),
                id='picklefield.E001',
            ),
            checks.Warning(
                msg=msg,
                hint='Use a callable instead, e.g., use `set` instead of `%s`.' % repr(set()),
                obj=Model._meta.get_field('set_field'),
                id='picklefield.E001',
            )
        ])

    def test_non_mutable_default_check(self):
        class Model(models.Model):
            list_field = PickledObjectField(default=list)
            dict_field = PickledObjectField(default=dict)
            set_field = PickledObjectField(default=set)

        self.assertEqual(Model().check(), [])
