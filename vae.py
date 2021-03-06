# -*- coding: utf-8 -*-
"""VAE.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_zKyo-2vQTirKO7Xfb_8QEruWuBAcfvj
"""

from __future__ import print_function
import argparse
import torch
import torch.utils.data
from torch import nn, optim
from torchvision import datasets, transforms
from torchvision.utils import save_image
from IPython.display import Image, display
import matplotlib.pyplot as plt

!mkdir results

batch_size = 100
latent_size = 20

cuda = torch.cuda.is_available()
device = torch.device("cuda" if cuda else "cpu")

kwargs = {'num_workers': 1, 'pin_memory': True} if cuda else {}
train_loader = torch.utils.data.DataLoader(
    datasets.MNIST('../data', train=True, download=True,
                   transform=transforms.ToTensor()),
    batch_size=batch_size, shuffle=True, **kwargs)
test_loader = torch.utils.data.DataLoader(
    datasets.MNIST('../data', train=False, transform=transforms.ToTensor()),
    batch_size=batch_size, shuffle=True, **kwargs)

len(test_loader)

class VAE(nn.Module):
    def __init__(self, x_dim = 784, h_dim = 400, latent_size = 20):
        super(VAE, self).__init__()
        #TODO
        # encoder 
        self.fc1 = nn.Linear(x_dim, h_dim)
        self.fc21 = nn.Linear(h_dim, latent_size)
        self.fc22 = nn.Linear(h_dim, latent_size)

        #decoder 
        self.fc3 = nn.Linear(latent_size, h_dim)
        self.fc4 = nn.Linear(h_dim, x_dim)

    def encode(self, x):
        #The encoder will take an input of size 784, and will produce two vectors of size latent_size (corresponding to the coordinatewise means and log_variances)
        #It should have a single hidden linear layer with 400 nodes using ReLU activations, and have two linear output layers (no activations)
        #TODO
        h = torch.nn.functional.relu(self.fc1(x))
        return self.fc22(h), self.fc22(h)

    def reparameterize(self, means, log_variances):
        #The reparameterization module lies between the encoder and the decoder
        #It takes in the coordinatewise means and log-variances from the encoder (each of dimension latent_size), and returns a sample from a Gaussian with the corresponding parameters
        #TODO
        std = torch.exp(0.5*log_variances)
        eps = torch.randn_like(std)
        return eps.mul(std).add_(means) # return z sample

    def decode(self, z):
        #The decoder will take an input of size latent_size, and will produce an output of size 784
        #It should have a single hidden linear layer with 400 nodes using ReLU activations, and use Sigmoid activation for its outputs
        #TODO
        h = torch.nn.functional.relu(self.fc3(z))
        return torch.sigmoid(self.fc4(h))

    def forward(self, x):
        #Apply the VAE encoder, reparameterization, and decoder to an input of size 784
        #Returns an output image of size 784, as well as the means and log_variances, each of size latent_size (they will be needed when computing the loss)
        #TODO
        means, log_variances = self.encode(x.view(-1,784))
        z = self.reparameterize(means, log_variances)
        return self.decode(z), means, log_variances

def vae_loss_function(reconstructed_x, x, means, log_variances):
    #Compute the VAE loss
    #The loss is a sum of two terms: reconstruction error and KL divergence
    #Use cross entropy loss between x and reconstructed_x for the reconstruction error (as opposed to L2 loss as discussed in lecture -- this is sometimes done for data in [0,1] for easier optimization)
    #The KL divergence is -1/2 * sum(1 + log_variances - means^2 - exp(log_variances)) as described in lecture
    #Returns loss (reconstruction + KL divergence) and reconstruction loss only (both scalars)
    #TODO
    reconstruction_loss = nn.functional.binary_cross_entropy(reconstructed_x, x.view(-1,784), reduction= 'sum')
    kl_divergence = -0.5 * torch.sum(1 + log_variances - means.pow(2) - log_variances.exp())
    loss = kl_divergence + reconstruction_loss 
    return loss, reconstruction_loss

def train(model, optimizer):
    #Trains the VAE for one epoch on the training dataset
    #Returns the average (over the dataset) loss (reconstruction + KL divergence) and reconstruction loss only (both scalars)
    #TODO
    model.train()

    train_loss = 0
    train_reconstruction_loss = 0

    for batch_idx, (data, _) in enumerate(train_loader):
      data = data.cuda()
      optimizer.zero_grad()
        
      recon_batch, mu, log_var = model(data)
      loss, reconstruction_loss = vae_loss_function(recon_batch, data, mu, log_var)

       
      loss.backward(retain_graph = True)
      #reconstruction_loss.backward()

      train_loss += loss.item()
      train_reconstruction_loss += reconstruction_loss.item()
      optimizer.step()
    

    return train_loss/len(train_loader.dataset), train_reconstruction_loss/len(train_loader.dataset)

def test(model):
    #Runs the VAE on the test dataset
    #Returns the average (over the dataset) loss (reconstruction + KL divergence) and reconstruction loss only (both scalars)
    #TODO

    model.eval()
    avg_test_loss= 0
    avg_test_reconstruction_loss = 0

    with torch.no_grad():
        for data, _ in test_loader:
            data = data.cuda()
            recon, mu, log_var = model(data)
            
            # sum up batch loss
            test_loss, test_reconstruction_loss = vae_loss_function(recon, data, mu, log_var)
            avg_test_loss += test_loss.item()
            avg_test_reconstruction_loss += test_reconstruction_loss.item()
        
    avg_test_loss /= len(test_loader.dataset)
    avg_test_reconstruction_loss /= len(test_loader.dataset)
    
    return avg_test_loss, avg_test_reconstruction_loss

epochs = 50
avg_train_losses = []
avg_train_reconstruction_losses = []
avg_test_losses = []
avg_test_reconstruction_losses = []

vae_model = VAE().to(device)
vae_optimizer = optim.Adam(vae_model.parameters(), lr=1e-3)

for epoch in range(1, epochs + 1):
    avg_train_loss, avg_train_reconstruction_loss = train(vae_model, vae_optimizer)
    avg_test_loss, avg_test_reconstruction_loss = test(vae_model)
    
    avg_train_losses.append(avg_train_loss)
    avg_train_reconstruction_losses.append(avg_train_reconstruction_loss)
    avg_test_losses.append(avg_test_loss)
    avg_test_reconstruction_losses.append(avg_test_reconstruction_loss)

    with torch.no_grad():
        sample = torch.randn(64, latent_size).to(device)
        sample = vae_model.decode(sample).cpu()
        save_image(sample.view(64, 1, 28, 28),
                   'results/sample_' + str(epoch) + '.png')
        print('Epoch #' + str(epoch))
        display(Image('results/sample_' + str(epoch) + '.png'))
        print('\n')

plt.plot(avg_train_reconstruction_losses)
plt.title('Training Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch #')
plt.show()

plt.plot(avg_test_reconstruction_losses)
plt.title('Test Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch #')
plt.show()

