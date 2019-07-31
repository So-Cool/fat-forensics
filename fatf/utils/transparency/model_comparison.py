"""
Implementation various measures for comparing local model to global model.
"""
# Author: Alex Hepburn <ah13558@bristol.ac.uk>
# License: new BSD

import numpy as np

import fatf
import fatf.utils.data.augmentation as fuda
import fatf.utils.models.metrics as fumm
import fatf.utils.models.validation as fumv
import fatf.utils.array.validation as fuav
from fatf.exceptions import IncompatibleModelError, IncorrectShapeError

__all__ = ['local_fidelity_score']


def _input_is_valid(dataset: np.ndarray,
                    data_row: np.ndarray,
                    local_model: object,
                    global_model: object,
                    r_fid: float,
                    samples_number: int):
    """
    Validates the input parameters of model comparison functions.

    For parameters descriptions and exceptions raised please see
    :func:`fatf.utils.transparency.model_comparison.local_fidelity_score`.

    Returns
    -------
    is_input_ok : boolean
        ``True`` if input is valid, ``False`` otherwise.
    """
    is_input_ok = False

    if not fuav.is_2d_array(dataset):
        raise IncorrectShapeError('The input dataset must be a '
                                  '2-dimensional numpy array.')
    if not fuav.is_base_array(dataset):
        raise TypeError('The input dataset must be of a base type.')

    is_structued = fuav.is_structured_array(dataset)

    if not fuav.is_1d_like(data_row):
        raise IncorrectShapeError('The data_row must either be a '
                                    '1-dimensional numpy array or numpy '
                                    'void object for structured rows.')

    are_similar = fuav.are_similar_dtype_arrays(
        dataset, np.array([data_row]), strict_comparison=True)
    if not are_similar:
        raise TypeError('The dtype of the data_row is different to '
                        'the dtype of the data array used to '
                        'initialise this class.')

    # If the dataset is structured and the data_row has a different
    # number of features this will be caught by the above dtype check.
    # For classic numpy arrays this has to be done separately.
    if not is_structured:
        if data_row.shape[0] != dataset.shape[1]:
            raise IncorrectShapeError('The data_row must contain the '
                                        'same number of features as the '
                                        'dataset used to initialise '
                                        'this class.')

    if not check_model_functionality(global_model, suppress_warning=True):
        raise IncompatibleModelError()

    if not check_model_functionality(local_model, suppress_warning=True):
        raise IncompatibleModelError()

    if not isinstance(r_fid, float):
            raise TypeError('r_fid must be float.')
    else:
        if r_fid <= 0.0:
            raise ValueError('r_fid must be a positive integer.')

    if isinstance(samples_number, int):
            if samples_number < 1:
                raise ValueError('The samples_number parameter must be a '
                                 'positive integer.')
    else:
        raise TypeError('The samples_number parameter must be an integer.')

    is_input_ok = True
    return is_input_ok


def local_fidelity_score(dataset: np.ndarray,
                         data_row: np.ndarray,
                         local_model: object,
                         global_model: object,
                         global_class: int,
                         r_fid=0.05,
                         samples_number=50) -> float:
    """
    Computes local fidelity score for an instance in a dataset.

    This function implements a adapted version of the local fidelity method
    introduced by [LAUGEL2018SPHERES]_. For a specific data point,
    it samples uniformally within a hypersphere with radius corresponding to a
    percentage of the maximum l-2 distance between the instance to generate
    around and all other instances in the dataset. It then computes
    probabilities that the instances belong to the ``global_class`` that the
    data_row belongs to. It then computes an agreement between these
    predictions using accuracy.

    .. [LAUGEL2018SPHERES] Laugel, T., Renard, X., Lesot, M. J., Marsala,
       C., & Detyniecki, M. (2018). Defining locality for surrogates in
       post-hoc interpretablity. Workshop on Human Interpretability for
       Machine Learning (WHI)-International Conference on Machine Learning,
       2018.

    Parameters
    ----------
    dataset : numpy.ndarray
        A 2-dimensional numpy array with a dataset to be used for sampling.
    data_row : numpy.ndarray
        A data point.
    local_model : object
        A trained local model that must be able to output predicted class
        via ``predict`` method.
    global_model : object
        A trained global model that must be able to output predicted class
        via ``predict`` method.
    global_class : integer
        The class which the probabilities belong to that the local model was
        trained to predict.
    r_fid : float, Optional (defualt=0.05)
        Radius of fideility which is the percentage of the maximum distance
        between any two dataponts in the dataset, which will be the radius
        of the l-2 hypersphere that points will be sampled in.
    samples_number : integer, Optional(default=50)
        The number of samples to be generated.

    Raises
    ------

    Returns
    -------
    accuracy : float
        Agreement between ``local_model`` predictions and ``global_model``
        predictions for the data sampled.
    """
    augmentor = fuda.LocalFidelity(dataset, int_to_float=True)
    sampled_data = augmentor.sample(data_row, r_fid, samples_number)

    local_predictions = local_model.predict(sampled_data)
    global_predictions = global_model.predict(sampled_data)

    local_predictions[local_predictions>0.5] = 1
    local_predictions[local_predictions<0.5] = 0

    class_indx = global_predictions == global_class
    global_predictions[class_indx] = 1
    global_predictions[~class_indx] = 0

    # TODO: maybe just write a function to compute accuracy
    # not from confusion matrix

    confusion_matrix = fumm.get_confusion_matrix(local_predictions,
                                                 global_predictions)
    if confusion_matrix.shape == (1, 1):
        accuracy = 1.0
    else:
        accuracy = fumm.accuracy(confusion_matrix)

    return accuracy
