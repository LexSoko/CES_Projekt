import math
import numpy as np
from tqdm import tqdm
from scipy import linalg


def power_method(B, tol=1e-5, maxit=1e8, x_0=None):
    """
    Calculation of the biggest eigenvector/value

    Algorithm computes the biggest eigenvector of the given array B, and the related eigenvalue.
    Furthermore the residuum of the calculated approximation is also computed. The returned eigenvector is normalized.

    Arguments:
        B (numpy array) -- square array to calculate eigenvectors and eigenvalues from

    Keyword Arguments:
        tol (float) -- lower limit for the residuum, algorithm stops if reached (default: {1e-5})
        maxit (float)   -- maximum number of iterations, algorithm stops if reached (default: {1e8})
        x_0 (numpy array)   -- starting vector, if none given a random one is chosen (default: {None})

    Returns:
        eigenvalue (float)
        eigenvector (numpy array)
        residuum (numpy array)
    """
    x = []
    residuum = []
    # set x_0 random, if no explicit vector is given
    if x_0 == None:
        x_0 = np.random.randint(low=1, high=255, size=(np.shape(B)[0]))
        x_0 = x_0 / np.linalg.norm(x_0)  # normalize
        x.append(x_0)

    # calculate eigenvectors
    i = 0
    while (
        i < maxit
    ):  # stop calculation if maximum number of allowed iterations is reached

        x_p = B.dot(x[-1])
        norm_p = np.linalg.norm(x_p)
        x_p = x_p / norm_p  # normalize
        x.append(x_p)

        xpc = x[-1].conjugate()
        xp = x[-1]
        xp_1c = x[-2].conjugate()
        xp_1 = x[-2]

        # calculate the residuum for the current eigenvektor
        residuum.append(
            np.abs(
                (xpc.dot(B.dot(xp)) / xpc.dot(xp))
                - (xp_1c.dot(B.dot(xp_1)) / xp_1c.dot(xp_1))
            )
        )

        if (
            residuum[-1] <= tol
        ):  # stop algorithm if residuum lower limit is reached
            break
        else:
            i += 1

    eigenvector = x_p
    eigenvalue = (
        (xpc.dot(B.dot(xp))) / (xpc.dot(xp)) / norm_p
    )  # compute related eigenvalue

    return eigenvalue, eigenvector, np.array(residuum)


def deflation(B, eigenvalue, eigenvector):  # matrix deflation
    return B - eigenvalue * np.outer(eigenvector, eigenvector.conjugate())


def eig_n(B, n, tol=1e-5, maxit=1e8, x_0=None, tqdmoff=True):
    """
    Calculation of the n-biggest eigenvector/value

    Algorithm computes the n-biggest eigenvector of the given array B, and the related eigenvalue.
    Furthermore the residuum of the calculated approximations are also computed. The returned eigenvectors are normalized.

    Arguments:
        B (numpy array) -- square array to calculate eigenvectors and eigenvalues from
        n (int) --  number of eigenvectors/values to be calculated

    Keyword Arguments:
        tol (float) -- lower limit for the residuum, algorithm stops if reached (default: {1e-5})
        maxit (float)   -- maximum number of iterations, algorithm stops if reached (default: {1e8})
        x_0 (numpy array)   -- starting vector, if none given a random one is chosen (default: {None})

    Returns:
        eigenvalue (numpy array)
        eigenvector (numpy array)
        residuum (numpy array)
    """

    eigenvalues = [0] * n
    eigenvectors = [0] * n
    residuum = [0] * n
    for i in tqdm(range(n), desc=f"{n}-eigenvalues", disable=tqdmoff):
        eigenvalue, eigenvector, residuum[i] = power_method(
            B, tol=tol, maxit=maxit, x_0=x_0
        )
        eigenvalues[i] = eigenvalue
        eigenvectors[i] = eigenvector

        B = deflation(B, eigenvalue, eigenvector)

    return (
        np.array(eigenvalues),
        np.array(eigenvectors).T,
        residuum,
    )


def svd_compression(E, n, tol=1e-5, maxit=1e8, tqdmoff=True):
    """
    SVD-compression of given matrix E

    Algorithm computes a svd-compressed version of matrix E

    Arguments:
        E (numpy array) -- array to compress
        n (int) --  number of eigenvectors to be calculated

    Keyword Arguments:
        tol (float) -- lower limit for the residuum, algorithm stops if reached (default: {1e-5})
        maxit (float)   -- maximum number of iterations, algorithm stops if reached (default: {1e8})

    Returns:
        A_comp (numpy array) -- svd-compressed array
    """

    # calculate the B matrix for each rgb-channel
    A = [0] * 3
    B = [0] * 3
    for i in range(3):
        A[i] = E[:, :, i]

    # calculation of square matrix B for each channel
    for i in tqdm(range(3), desc="calculating Matrix B", disable=tqdmoff):
        B[i] = A[i].transpose().conjugate().dot(A[i])

    ######      calculation of V        #######
    # calculate n-eigenvectors for each channel
    eigenvalues = [0] * 3
    eigenvectors = [0] * 3
    for i in tqdm(range(3), desc="calculating eigenvectors", disable=tqdmoff):
        eigenvalues[i], eigenvectors[i], residuum = eig_n(
            B[i], n, tol=tol, maxit=maxit
        )

    # construct matrix V
    V = eigenvectors
    for i in range(
        3
    ):  # check if eigenvector are orthonormal, if not they get orthonormalized via gram-schmidt
        W = V[i].T
        while not test_orthonormality(W):
            W = gram_schmidt(W)

        V[i] = W.T

    #####           calculation of D            #####
    D = [0] * 3
    for i in tqdm(range(3), desc="calculation of D", disable=tqdmoff):
        D[i] = np.diag(eigenvalues[i])

    ####            calculation of Lambda       #####
    L = [0] * 3
    for i in range(3):
        L[i] = linalg.sqrtm(D[i])

    ####            calculation of U compressed       #####
    U = [0] * 3
    for i in range(3):
        U[i] = A[i].dot(V[i].dot(linalg.sqrtm(np.linalg.inv(D[i]))))

    ####            calculation of A compressed       #####
    A_comp = [0] * 3

    for i in range(3):
        A_comp[i] = U[i].dot(L[i].dot(V[i].conjugate().T))
        A_comp[i] = (A_comp[i] / A_comp[i].max()) * 255
        img_comp = A_comp[i]
        img_comp[img_comp < 0] = 0
        img_comp[img_comp > 255] = 255
    A_comp = np.array(A_comp)
    A_comp = np.swapaxes(A_comp, 0, 2)
    A_comp = np.swapaxes(A_comp, 0, 1)

    return A_comp


def test_orthonormality(basis_matrix: np.ndarray, **kwargs):
    """
    tests basis vectors for orthonormality

    Arguments:
        basis_matrix -- matrix consisting of basis vectors in form [bv1,bv2,bv3,0_vect,...,0_vect] where 0_vect is a vector consisting of zeros. the basis matrix must be square.
        num_ev -- number of actual basis vectors bvi.

    Keyword Argumends:
        rel_tol -- is the relative tolerance – it is the maximum allowed difference between a and b, relative to the larger absolute value of a or b. For example, to set a tolerance of 5%, pass rel_tol=0.05. The default tolerance is 1e-09, which assures that the two values are the same within about 9 decimal digits. rel_tol must be greater than zero.
        abs_tol -- is the minimum absolute tolerance – useful for comparisons near zero. abs_tol must be at least zero.

    Returns:
        True if the basis vectors are maybe orthogonal (not sure of the algorithm yet)
    """
    n_vec, n_base = basis_matrix.shape
    W = np.pad(
        basis_matrix,
        ((0, n_base - n_vec), (0, 0)),
        mode="constant",
        constant_values=0,
    )
    I = W.dot(W.T)
    return math.isclose(np.sum(I), n_vec, **kwargs) and math.isclose(
        np.trace(I), n_vec, **kwargs
    )


def gram_schmidt(bm: np.ndarray):
    """
    creates new orthonormal basis vectors out of the given basis vectors

    Arguments:
        basis_matrix -- matrix consisting of basis vectors in form [bv1,bv2,bv3,..., bvn].
    """
    n_vec, k_base = bm.shape

    nbm: np.ndarray = np.zeros((n_vec, k_base))
    nbm[0] = bm[0] / np.linalg.norm(bm[0])

    for k in range(1, n_vec):
        nbm[k] = bm[k] - (bm[k].dot(nbm[0]) / nbm[0].dot(nbm[0])) * nbm[0]

        for p in range(1, k):
            nbm[k] = (
                nbm[k] - (nbm[k].dot(nbm[p]) / nbm[p].dot(nbm[p])) * nbm[p]
            )

        nbm[k] = nbm[k] / np.linalg.norm(nbm[k])

    return nbm
