"""
Functions for testing data discretiser classes.
"""
# Author: Alex Hepburn <ah13558@bristol.ac.uk>
# License: new BSD

import pytest

import numpy as np

import fatf

from fatf.exceptions import IncorrectShapeError

import fatf.utils.data.discretization as fudd

# yapf: disable
NUMERICAL_NP_ARRAY = np.array([
    [0, 0, 0.08, 0.69],
    [1, 0, 0.03, 0.29],
    [0, 1, 0.99, 0.82],
    [2, 1, 0.73, 0.48],
    [1, 0, 0.36, 0.89],
    [0, 1, 0.07, 0.21]])
NUMERICAL_3D_ARRAY = np.ones((2, 2, 2))
NUMERICAL_STRUCT_ARRAY = np.array(
    [(0, 0, 0.08, 0.69),
     (1, 0, 0.03, 0.29),
     (0, 1, 0.99, 0.82),
     (2, 1, 0.73, 0.48),
     (1, 0, 0.36, 0.89),
     (0, 1, 0.07, 0.21)],
    dtype=[('a', 'i'), ('b', 'i'), ('c', 'f'), ('d', 'f')])
CATEGORICAL_NP_ARRAY = np.array([
    ['a', 'b', 'c'],
    ['a', 'f', 'g'],
    ['b', 'c', 'c'],
    ['b', 'f', 'c'],
    ['a', 'f', 'c'],
    ['a', 'b', 'g']])
CATEGORICAL_STRUCT_ARRAY = np.array(
    [('a', 'b', 'c'),
     ('a', 'f', 'g'),
     ('b', 'c', 'c'),
     ('b', 'f', 'c'),
     ('a', 'f', 'c'),
     ('a', 'b', 'g')],
    dtype=[('a', 'U1'), ('b', 'U1'), ('c', 'U1')])
MIXED_ARRAY = np.array(
    [(0, 'a', 0.08, 'a'),
     (0, 'f', 0.03, 'bb'),
     (1, 'c', 0.99, 'aa'),
     (1, 'a', 0.73, 'a'),
     (0, 'c', 0.36, 'b'),
     (1, 'f', 0.07, 'bb')],
    dtype=[('a', 'i'), ('b', 'U1'), ('c', 'f'), ('d', 'U2')])
# yapf: enable


def test_validate_input():
    """
    Tests :func:`fatf.utils.data.discretization._validate_input` function.
    """
    incorrect_shape_data = ('The input dataset must be a 2-dimensional numpy '
                            'array.')
    type_error_data = 'The input dataset must be of a base type.'
    index_error_cidx = ('The following indices are invalid for the input '
                        'dataset: {}.')
    type_error_cidx = ('The categorical_indices parameter must be a Python '
                       'list or None.')

    with pytest.raises(IncorrectShapeError) as exin:
        fudd._validate_input(np.array([0, 4, 3, 0]))
    assert str(exin.value) == incorrect_shape_data

    with pytest.raises(TypeError) as exin:
        fudd._validate_input(np.array([[0, 4], [None, 0]]))
    assert str(exin.value) == type_error_data

    #

    with pytest.raises(TypeError) as exin:
        fudd._validate_input(NUMERICAL_NP_ARRAY, categorical_indices=0)
    assert str(exin.value) == type_error_cidx

    with pytest.raises(IndexError) as exin:
        fudd._validate_input(MIXED_ARRAY, categorical_indices=['f'])
    assert str(exin.value) == index_error_cidx.format(['f'])
    with pytest.raises(IndexError) as exin:
        fudd._validate_input(MIXED_ARRAY, categorical_indices=[1])
    assert str(exin.value) == index_error_cidx.format([1])

    #
    assert fudd._validate_input(
        MIXED_ARRAY,
        categorical_indices=['a', 'b'])


class TestDiscretiser():
    """
    Tests :class:`fatf.utils.data.discretize.Discretizer` abstract class.
    """

    class BrokenDiscretizer1(fudd.Discretizer):
        """
        A broken data augmentation implementation.

        This class does not have a ``sample`` method.
        """

        def __init__(self, dataset, categorical_indices=None):
            """
            Dummy init method.
            """
            super().__init__(  # pragma: nocover
                dataset,
                categorical_indices=categorical_indices)

    class BrokenDiscretizer2(fudd.Discretizer):
        """
        A broken data augmentation implementation.

        This class does not have a ``sample`` method.
        """

    class BaseDiscretizer(fudd.Discretizer):
        """
        A dummy data discretizer implementation.

        For :func:`fatf.utils.data.discretization._validate_input` and
        :func:`~fatf.utils.data.augmentation.discretization._validate_
        discretize_input` testing.
        """

        def __init__(self, dataset, categorical_indices=None):
            """
            Dummy init method.
            """
            super().__init__(dataset, categorical_indices=categorical_indices)

        def discretize(self, data):
            """
            Dummy sample method.
            """
            self._validate_discretize_input(data)
            return np.ones(data.shape)

    def test_discretizer_class_init(self):
        """
        Tests :class:`fatf.utils.data.discretization.Discretizer` class init.
        """
        abstract_method_error = ("Can't instantiate abstract class "
                                 '{} with abstract methods discretize')
        user_warning = (
            'Some of the string-based columns in the input dataset were not '
            'selected as categorical features via the categorical_indices '
            'parameter. String-based columns cannot be treated as numerical '
            'features, therefore they will be also treated as categorical '
            'features (in addition to the ones selected with the '
            'categorical_indices parameter).')

        with pytest.raises(TypeError) as exin:
            self.BrokenDiscretizer1(NUMERICAL_NP_ARRAY)
        msg = abstract_method_error.format('BrokenDiscretizer1')
        assert str(exin.value) == msg

        with pytest.raises(TypeError) as exin:
            self.BrokenDiscretizer2(NUMERICAL_NP_ARRAY)
        msg = abstract_method_error.format('BrokenDiscretizer2')
        assert str(exin.value) == msg

        with pytest.raises(TypeError) as exin:
            fudd.Discretizer(NUMERICAL_NP_ARRAY)
        assert str(exin.value) == abstract_method_error.format('Discretizer')

        # Test for a categorical index warning
        with pytest.warns(UserWarning) as warning:
            discretizer = self.BaseDiscretizer(CATEGORICAL_NP_ARRAY, [0])
        assert len(warning) == 1
        assert str(warning[0].message) == user_warning
        assert np.array_equal(discretizer.categorical_indices, [0, 1, 2])
        #
        with pytest.warns(UserWarning) as warning:
            discretizer = self.BaseDiscretizer(CATEGORICAL_STRUCT_ARRAY, ['a'])
        assert len(warning) == 1
        assert str(warning[0].message) == user_warning
        assert np.array_equal(discretizer.categorical_indices,
                              np.array(['a', 'b', 'c']))
        #
        with pytest.warns(UserWarning) as warning:
            discretizer = self.BaseDiscretizer(MIXED_ARRAY, ['b'])
        assert len(warning) == 1
        assert str(warning[0].message) == user_warning
        assert np.array_equal(discretizer.categorical_indices, ['b', 'd'])

        # Validate internal variables
        categorical_np_discretizer = self.BaseDiscretizer(CATEGORICAL_NP_ARRAY)
        assert np.array_equal(categorical_np_discretizer.dataset,
                              CATEGORICAL_NP_ARRAY)
        assert not categorical_np_discretizer.is_structured
        assert categorical_np_discretizer.categorical_indices == [0, 1, 2]
        assert categorical_np_discretizer.numerical_indices == []
        assert categorical_np_discretizer.features_number == 3

        categorical_struct_discretizer = self.BaseDiscretizer(
            CATEGORICAL_STRUCT_ARRAY)
        assert np.array_equal(categorical_struct_discretizer.dataset,
                              CATEGORICAL_STRUCT_ARRAY)
        assert categorical_struct_discretizer.is_structured
        assert (categorical_struct_discretizer.categorical_indices
                == ['a', 'b', 'c'])  # yapf: disable
        assert categorical_struct_discretizer.numerical_indices == []
        assert categorical_struct_discretizer.features_number == 3

        mixed_discretizer = self.BaseDiscretizer(MIXED_ARRAY)
        assert np.array_equal(mixed_discretizer.dataset, MIXED_ARRAY)
        assert mixed_discretizer.is_structured
        assert mixed_discretizer.categorical_indices == ['b', 'd']
        assert mixed_discretizer.numerical_indices == ['a', 'c']
        assert mixed_discretizer.features_number == 4

        numerical_np_discretizer = self.BaseDiscretizer(NUMERICAL_NP_ARRAY, [0, 1])
        assert np.array_equal(numerical_np_discretizer.dataset,
                              NUMERICAL_NP_ARRAY)
        assert not numerical_np_discretizer.is_structured
        assert numerical_np_discretizer.categorical_indices == [0, 1]
        assert numerical_np_discretizer.numerical_indices == [2, 3]
        assert numerical_np_discretizer.features_number == 4

    def test_discretizer_sample_validation(self):
        """
        Tests :func:`~fatf.utils.data.discretization.Discretizer.
        discretize` method.

        This function test validation of input for the ``discretize`` method.
        """
        incorrect_shape_data_row = ('data must be a 1-dimensional array, '
                                    '2-dimensional array or void object for '
                                    'structured rows.')
        type_error_data_row = ('The dtype of the data is different to the '
                               'dtype of the data array used to initialise '
                               'this class.')
        incorrect_shape_features = ('The data must contain the same number of '
                                    'features as the dataset used to '
                                    'initialise this class.')

        # Validate sample input rows
        numerical_np_discretizer = self.BaseDiscretizer(NUMERICAL_NP_ARRAY)
        categorical_np_discretizer = self.BaseDiscretizer(CATEGORICAL_NP_ARRAY)
        numerical_struct_discretizer = self.BaseDiscretizer(NUMERICAL_STRUCT_ARRAY)
        categorical_struct_discretizer = self.BaseDiscretizer(
            CATEGORICAL_STRUCT_ARRAY, categorical_indices=['a', 'b', 'c'])

        # data_row shape
        with pytest.raises(IncorrectShapeError) as exin:
            numerical_np_discretizer.discretize(NUMERICAL_3D_ARRAY)
        assert str(exin.value) == incorrect_shape_data_row

        # 1-D data
        # data type
        with pytest.raises(TypeError) as exin:
            numerical_np_discretizer.discretize(np.array(['a', 'b', 'c', 'd']))
        assert str(exin.value) == type_error_data_row
        with pytest.raises(TypeError) as exin:
            numerical_struct_discretizer.discretize(MIXED_ARRAY[0])
        assert str(exin.value) == type_error_data_row
        with pytest.raises(TypeError) as exin:
            categorical_np_discretizer.discretize(np.array([0.1]))
        assert str(exin.value) == type_error_data_row
        # Structured too short
        with pytest.raises(TypeError) as exin:
            numerical_struct_discretizer.discretize(MIXED_ARRAY[['a', 'b']][0])
        assert str(exin.value) == type_error_data_row

        # data features number
        with pytest.raises(IncorrectShapeError) as exin:
            numerical_np_discretizer.discretize(np.array([0.1, 1, 2]))
        assert str(exin.value) == incorrect_shape_features
        with pytest.raises(IncorrectShapeError) as exin:
            categorical_np_discretizer.discretize(np.array(['a', 'b']))
        assert str(exin.value) == incorrect_shape_features

        # 2-D data
        
