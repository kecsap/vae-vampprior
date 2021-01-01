import tensorflow as tf
import tensorflow_probability as tfp

from vampprior.layers import Encoder, Decoder, Sampling, MeanReducer
from vampprior.probabilities import log_normal_diag


class VAE(tf.keras.Model):
    def __init__(self, D, L, **kwargs):
        super(VAE, self).__init__(**kwargs)
        self.D = D
        self.L = L

    def build(self, inputs_shape):
        self.encoder = Encoder(self.D)
        self.sampling = Sampling(self.D, self.L)
        self.decoder = Decoder((inputs_shape[1], inputs_shape[2]))
        self.mean_reducer = MeanReducer()

    def call(self, inputs):
        mu, logvar = self.encoder(inputs)
        samples = self.sampling((mu, logvar))

        # TODO: improve numerical stability and remove epsilon
        #   to improve decoding performances

        # epsilon for avoiding log explosion in loss
        eps = 1e-18

        # loss due to regularization
        # first addend, corresponding to log( p_lambda (z_phi^l) )
        normal_standard = tfp.distributions.MultivariateNormalDiag(tf.zeros(self.D), tf.ones(self.D))
        log_p_lambda = tf.math.log(eps + normal_standard.prob(samples))

        # second addend, corresponding to log( q_phi (z|x) )
        # where q_phi=N(z| mu_phi(x), sigma^2_phi(x))
        # samples have shape (N, L, D) where N is the minibatch size and D the latent var dimension
        log_q_phi = log_normal_diag(samples, mu, logvar, reduce_dim=2)

        regularization_loss = tf.math.subtract(tf.math.reduce_mean(log_q_phi),
                                               tf.math.reduce_mean(log_p_lambda),
                                               name='regularization-loss')
        self.add_loss(regularization_loss)

        reconstructed = self.decoder(samples)

        # return reconstructed
        return self.mean_reducer(reconstructed)

    def generate(self, N):
        normal_standard = tfp.distributions.MultivariateNormalDiag(tf.zeros((self.D,)),
                                                                   tf.ones((self.D,)))
        samples = normal_standard.sample([N])

        # inputs will have shape (N, D)
        reconstructed = self.decoder(samples)

        # aggregation still needed as result will have shape (N, 1, M, M)
        # in order to remove the 1-st axis
        return self.mean_reducer(reconstructed)


class VampVAE():
    # TODO
    pass


class MixtureVAE():
    # TODO
    pass


class HVAE():
    # TODO
    pass
