import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

from vampprior.models import VAE, VampVAE

parser = argparse.ArgumentParser(description='VAE+VampPrior')
# Model params
parser.add_argument('--model-name', '-mn', type=str, default='vae', metavar='model_name',
                    help='model name: vae, vamp', choices=['vae', 'vamp'])
parser.add_argument('-C', '--pseudo-inputs', type=int, default=300, metavar='C',
                    help='number of pseudo-inputs with vamp prior')
parser.add_argument('-D', type=int, default=40, metavar='D',
                    help='number of stochastic hidden units, i.e. z size (same for z1 and z2 with HVAE)')
# Training params
parser.add_argument('--epochs', '-e', type=int, default=1, metavar='epochs',
                    help='number of epochs')
parser.add_argument('-bs', '--batch-size', type=int, default=100, metavar='batch_size',
                    help='size of training mini-batch')
parser.add_argument('-L', type=int, default=1, metavar='L',
                    help='number of MC samples')
parser.add_argument('-lr', '--learning-rate', type=float, default=1e-3, metavar='lr',
                    help='learning rate')
# Debugging params
parser.add_argument('-tb', '--tensorboard', action='store_true', dest='tb',
                    help='save training log in ./ for tensorboard inspection')
parser.set_defaults(tb=False)
parser.add_argument('-d', '--debug', action='store_true', dest='debug',
                    help='show images')
parser.set_defaults(debug=False)

args = parser.parse_args()

log_dir = './'  # save tensorboard logs in the current dir


def train_test_vae(vae, x_train, x_test, epochs, batch_size,
                   model_name, show=True, tb=False):
    """
    Train model and visualize result
    """
    callbacks = None
    if tb:
        callbacks = [tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)]

    vae.fit(x_train, x_train, epochs=epochs, batch_size=batch_size, callbacks=callbacks)

    print("Now testing reconstruction")
    reconstructions = vae(x_test[:5])

    plt.title(f"Reconstruction for {model_name}")
    for i, reconstruction in enumerate(reconstructions):
        plt.subplot(2, 5, 1 + i)
        plt.imshow(x_test[i])

        plt.subplot(2, 5, 6 + i)
        plt.imshow(reconstruction)

    if show:
        plt.show()
    else:
        # create folder to save images if it does not exists
        if not os.path.exists("img"):
            os.mkdir("img")

        plt.savefig(os.path.join("img", f"{model_name}-reconstructions.png"))

    print("Now testing generation")
    generations = vae.generate(5)

    plt.title(f"Generations for {model_name}")
    for i, generation in enumerate(generations):
        plt.subplot(1, 5, 1 + i)
        plt.imshow(generation)

    if show:
        plt.show()
    else:
        plt.savefig(os.path.join("img", f"{model_name}-generations.png"))


def main():
    assert len(tf.config.list_physical_devices('GPU')) > 0

    mnist = tf.keras.datasets.mnist
    (mnist_train, _), (mnist_test, _) = mnist.load_data()

    # simple workaround for working with binary data
    # where each pixel is either 0 or 1
    # TODO: use correct dataset
    mnist_train = np.array((mnist_train / 255.) > 0.5, dtype=np.float32)
    mnist_test = np.array((mnist_test / 255.) > 0.5, dtype=np.float32)

    if args.model_name == 'vae':
        # simple VAE, normal standard prior
        model = VAE(args.D, args.L)
    elif args.model_name == 'vamp':
        # VAE with Vamp prior
        model = VampVAE(args.D, args.L, args.C)
    else:
        raise Exception('Wrong model name!')

    model.compile(optimizer=tf.keras.optimizers.Adam(lr=args.lr),
                  loss=tf.nn.sigmoid_cross_entropy_with_logits)

    train_test_vae(model, mnist_train, mnist_test,
                   args.epochs, args.batch_size, model_name=args.model_name, show=args.debug, tb=args.tb)

    return


if __name__ == "__main__":
    main()
