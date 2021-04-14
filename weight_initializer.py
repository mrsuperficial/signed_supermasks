
from typing import Tuple
import tensorflow as tf
import numpy as np
import pickle
import pickletools
from copy import copy

class initializer:
    """Use this class to initialize weights of some tensorflow/keras model
    """
    
    def __init__(self, seed=7531):
        print("initializer")

        self.seed = seed
        np.random.seed(self.seed)
        tf.random.set_seed(self.seed)
        
    def get_fans(self, shape: tuple) -> Tuple[int, int]:
        """Get fan_in, fan_out of a layer with given shape

        Args:
            shape (tuple): shape of layer

        Returns:
            Tuple[int, int]: fan_in, fan_out of given shape
        """
        fan_in = float(shape[-2]) if len(shape) > 1 else float(shape[-1])
        fan_out = float(shape[-1])
        for dim in shape[:-2]:
            fan_in *= float(dim)
            fan_out *= float(dim)
        return fan_in, fan_out

        
    def initialize_weights(self, 
                           dist: str, 
                           shape: tuple, 
                           mu=0, 
                           sigma=1, 
                           factor=1., 
                           mu_bi=[0,0], 
                           sigma_bi=[0,0], 
                           constant=1) -> np.ndarray:
        """Initializes weights for a given shape

        Args:
            dist (str): distribution from which the weight values are drawn
            shape (tuple): shape of weights to be initialized
            mu (int, optional): mean of distribution from which weights are drawn. Defaults to 0.
            sigma (int, optional): standard deviation from which weights are drawn. 
                                   Negative integers set sigma to a fan_in/fan_out variant such as He/Xavier. Defaults to 1.
            factor ([type], optional): constant by which initialized weights are multiplied with. Defaults to 1..
            mu_bi (list, optional): further specifies mean if dist == "bimodal_normal". Defaults to [0,0].
            sigma_bi (list, optional): further specified standard deviation if dist == "bimodal_normal". Defaults to [0,0].
            constant (int, optional): If weights are initialized to a constant, this variable further defines which constant should be chosen. Defaults to 1.

        Returns:
            np.ndarray: initialized weights in given shape
        """
        if dist == "std_normal":
            return np.random.randn(*shape)
        if dist == "bimodal_normal":
            norm = mu + sigma * np.random.randn(*shape)
            norm_pos = np.where(norm >= 0)
            norm_neg = np.where(norm < 0)

            if mu_bi[0] == 0 and mu_bi[1] == 0:
                mu_neg = norm[norm_neg].mean()
                mu_pos = norm[norm_pos].mean()
            else:
                mu_neg = mu_bi[0]
                mu_pos = mu_bi[1]

            if sigma_bi[0] == 0 and sigma_bi[1] == 0:
                sigma_neg = norm[norm_neg].std()
                sigma_pos = norm[norm_pos].std()
            else:
                sigma_neg = sigma_bi[0]
                sigma_pos = sigma_bi[1]
            
            print(f"Positive: mu={mu_pos}, sigma={sigma_pos}")
            print(f"Negative: mu={mu_neg}, sigma={sigma_neg}")

            norm[norm_pos] = mu_pos + sigma_pos * np.random.randn(*norm_pos[0].shape)
            norm[norm_neg] = mu_neg + sigma_neg * np.random.randn(*norm_neg[0].shape)

            return norm
        
        if dist == "uniform":
            if sigma < 0:
                
                fan_in, fan_out = self.get_fans(shape)
                

                if sigma == -1:
                    sigma = 2.0 / (fan_in + fan_out)
                if sigma == -2:
                    sigma = 1.0 / fan_in
                if sigma == -3:
                    sigma = 1.0 / fan_out
                if sigma == -4:
                    sigma = 2.0 / fan_in
                if sigma == -5:
                    sigma = 2.0 / fan_out
                if sigma == -6:
                    sigma = 3.0 / fan_out
                if sigma == -7: 
                    sigma = np.sqrt(6) / np.sqrt(fan_in + fan_out)
                if sigma == -8:
                    sigma = np.sqrt(6) / np.sqrt(fan_in)
                
                sigma *= factor

                return np.random.uniform(-sigma, sigma, shape)
            else:
                return np.random.uniform(-mu,mu,shape)
        
        if dist == "positive_uniform":
            uniform = self.initialize_weights(dist="uniform", 
                                              shape=shape, 
                                              mu=mu, 
                                              sigma=sigma, 
                                              factor=factor, 
                                              mu_bi=mu_bi, 
                                              sigma_bi=sigma_bi, 
                                              constant=constant)

            return np.abs(uniform)

        if dist == "normal":
            if sigma < 0:

                fan_in, fan_out = self.get_fans(shape)
                
                if sigma == -1:
                    sigma = 2.0 / (fan_in + fan_out)
                if sigma == -2:
                    sigma = 1.0 / fan_in
                if sigma == -3:
                    sigma = 1.0 / fan_out
                if sigma == -4:
                    sigma = np.sqrt(2.0) / np.sqrt(fan_in)
                if sigma == -5:
                    sigma = 2.0 / fan_out
                if sigma == -6:
                    sigma = 3.0 / fan_out
                if sigma == -7: 
                    sigma = np.sqrt(6) / np.sqrt(fan_in + fan_out)
                if sigma == -8:
                    sigma = np.sqrt(6) / np.sqrt(fan_in)

                sigma *= factor

            return mu + sigma*np.random.randn(*shape)
        if dist == "zeros":
            return np.zeros(shape)
        if dist == "ones":
            print("Ones")
            return np.ones(shape)
        if dist == "constant":

            fan_in, fan_out = self.get_fans(shape)

            if sigma == -1:
                sigma = 2.0 / (fan_in + fan_out)
            elif sigma == -2:
                sigma = 1.0 / fan_in
            elif sigma == -3:
                sigma = 1.0 / fan_out
            elif sigma == -4:
                sigma = 2.0 / fan_in
            elif sigma == -5:
                sigma = 2.0 / fan_out
            elif sigma == -6:
                sigma = 3.0 / fan_out
            elif sigma == -7:
                sigma = np.sqrt(2) / np.sqrt(fan_in + fan_out)
            elif sigma == -8:
                sigma = np.sqrt(2) / np.sqrt(fan_in)

            sigma *= factor

            
            return np.ones(shape) * sigma

        if dist == "signed_constant":
            
            fan_in, fan_out = self.get_fans(shape)
            

            if sigma == -1:
                sigma = 2.0 / (fan_in + fan_out)
            elif sigma == -2:
                sigma = 1.0 / fan_in
            elif sigma == -3:
                sigma = 1.0 / fan_out

            elif sigma == -4:
                sigma = np.sqrt(2) / np.sqrt(fan_in)
            elif sigma == -5:
                sigma = 2.0 / fan_out
            elif sigma == -6:
                sigma = 3.0 / fan_out

            elif sigma == -7: 
                sigma = np.sqrt(2) / np.sqrt(fan_in + fan_out)

            elif sigma == -8:
                sigma = np.sqrt(2) / np.sqrt(fan_in)
            
            sigma *= factor


            if constant == -1:
                norm_glorot = mu + sigma*np.random.randn(*shape)

                norm_glorot_pos = norm_glorot[np.where(norm_glorot > 0)]
                norm_glorot_neg = norm_glorot[np.where(norm_glorot < 0)]


                norm_glorot[norm_glorot >= mu] = np.mean(norm_glorot_pos)
                norm_glorot[norm_glorot < mu] = np.mean(norm_glorot_neg)

                return norm_glorot

            elif constant == -2:
                norm = mu + sigma*np.random.randn(*shape)
                norm[norm >= mu] = sigma
                norm[norm < mu] = -sigma

                return norm


    def set_weights_man(self, 
                        model: tf.keras.Model, 
                        layers=None, 
                        mode="normal", 
                        mu=0, 
                        sigma=0.05, 
                        factor=1., 
                        constant=1, 
                        set_mask=False,
                        mu_bi=[0,0], 
                        sigma_bi=[0,0], 
                        save_to="", 
                        save_suffix="", 
                        weight_as_constant=False, 
                        layer_shapes=None):
        """Set weights of a given tf model manually (in contrast to letting tensorflow/keras set the weights)

        Args:
            model (tf.keras.Model): model for which weights need to be set
            layers (list, optional): specify specific layers of model whose weights need to be set. If layers != None 
            those layers that are not contained in this list will be ignored. Defaults to None.
            mode (str, optional): distribution of weight initialization. Defaults to "normal".
            mu (int, optional): mean of distribution. Defaults to 0.
            sigma (float, optional): standard deviation of distribution. Defaults to 0.05.
            factor (float, optional): constant initialized weights get multiplied with. Defaults to 1..
            constant (int, optional): [description]. Defaults to 1.
            set_mask (bool, optional): if True, function will set mask weights. If False, function will set "weight weights". Defaults to False.
            mu_bi (list, optional): if mode == "bimodal_normal" mu_bi specifies the distribution. Otherwise ignored. Defaults to [0,0].
            sigma_bi (list, optional): if mode == "bimodal_normal" sigmi_bi specifies the distribution. 
                                       Otherwise ignored. Defaults to [0,0].
            save_to (str, optional): if weights should be saved to a file, specify file path here. 
                                    If not specified, weights will not be saved. Defaults to "".
            save_suffix (str, optional): optional suffix to filename. Defaults to "".
            weight_as_constant (bool, optional): specifies whether the weights should be set to frozen. Defaults to False.
            layer_shapes (list, optional): list of layer shapes. Defaults to None.

        Returns:
            model (tf.keras.Model): model with newly initialized weights
            initialized_weights (list): list of initialized weights
        """
        #i = 0

        initial_weights = []

        if layers == None:
            if weight_as_constant == False:
                layer_shape_counter = 0
                for l in model.layers:
                    
                    if l.type == "fefo":
                        W = self.initialize_weights(mode, 
                                                    [l.input_dim, l.units], 
                                                    mu=mu, 
                                                    sigma=sigma, 
                                                    factor=factor,
                                                    mu_bi=mu_bi, 
                                                    sigma_bi=sigma_bi, 
                                                    constant=constant)
                        if set_mask is False:
                            b = self.initialize_weights("ones", [l.units])
                            initial_weights.append([W,b])
                            # l.set_weights([W,b])
                            # l.set_weights([W])
                            l.set_normal_weights(W)
                            l.trainable = False
                        else:
                            initial_weights.append([W])
                            l.set_mask(W)
                            # l.set_weights([W])
                    elif l.type == "conv":
                        W = self.initialize_weights(mode, 
                                                    list(l.weight_shape), 
                                                    mu=mu, 
                                                    sigma=sigma, 
                                                    factor=factor,
                                                    mu_bi=mu_bi, 
                                                    sigma_bi=sigma_bi, 
                                                    constant=constant)
                        if set_mask is False:
                            b = self.initialize_weights("ones", [1,l.filters])
                            initial_weights.append([W,b])
                            # l.set_weights([W,b])
                            # l.set_weights([W])
                            l.set_normal_weights(W)
                            l.trainable = False


                        else:
                            initial_weights.append([W])
                            l.set_mask(W)
                    elif l.type == "fefo_normal":
                        W = self.initialize_weights(mode, 
                                                    layer_shapes[layer_shape_counter], 
                                                    mu=mu, 
                                                    sigma=sigma, 
                                                    factor=factor,
                                                    mu_bi=mu_bi, 
                                                    sigma_bi=sigma_bi, 
                                                    constant=constant)
                        l.set_weights([W])
                        layer_shape_counter += 1
                    elif l.type == "conv_normal":
                        W = self.initialize_weights(mode, 
                                                    layer_shapes[layer_shape_counter], 
                                                    mu=mu, 
                                                    sigma=sigma, 
                                                    factor=factor,
                                                    mu_bi=mu_bi, 
                                                    sigma_bi=sigma_bi, 
                                                    constant=constant)
                        l.set_weights([W])
                        layer_shape_counter += 1

                    else:
                        continue
            else:
                for l in model.layers:
                    if l.type == "fefo":
                        W = self.initialize_weights(mode, 
                                                    [l.input_dim, l.units], 
                                                    mu=mu, 
                                                    sigma=sigma, 
                                                    factor=factor,
                                                    mu_bi=mu_bi, 
                                                    sigma_bi=sigma_bi, 
                                                    constant=constant)
                        initial_weights.append(W)
                        l.set_normal_weights(W)
                    elif l.type == "conv":
                        W = self.initialize_weights(mode, 
                                                    list(l.weight_shape), 
                                                    mu=mu, 
                                                    sigma=sigma, 
                                                    factor=factor, 
                                                    mu_bi=mu_bi, 
                                                    sigma_bi=sigma_bi, 
                                                    constant=constant)
                        initial_weights.append(W)
                        l.set_normal_weights(W)
                    else:
                        continue
        else:
            layer_counter = 0
            for l in model.layers:
                if l.type is "fefo" or l.type is "conv":
                    W = layers[layer_counter]
                    l.set_weights([W])
                    layer_counter += 1
                # elif l.type is "conv":
                #     W = layer
                else:
                    continue

        if save_to != "":

            with open(save_to+save_suffix+".pkl", 'wb') as handle:
                pickled = pickle.dumps(initial_weights)
                optimized_pickle = pickletools.optimize(pickled)
                handle.write(optimized_pickle)


        return model, initial_weights

    def set_loaded_weights(self, 
                           model: tf.keras.Model, 
                           path:str) -> tf.keras.Model:
        """Sets weights of a specified model from a file

        Args:
            model (tf.keras.Model): model for which the weights need to be specified
            path (str): path to file which holds the weights

        Returns:
            tf.keras.Model: model with set weights
        """

        with open(path, "rb") as f:
            p = pickle.Unpickler(f)
            initial_weights = p.load()
        
        mask_flag = True if "mask" in path else False
        
        layer_counter = 0
        mask_layers = ["fefo", "conv"]
        normal_layers = ["fefo_normal", "conv_normal"]

        for layer in model.layers:
            if layer.type in mask_layers:
                if mask_flag:
                    layer.set_mask(initial_weights[layer_counter][0])
                else:
                    layer.set_normal_weights(initial_weights[layer_counter][0])
                layer_counter += 1
                
            elif layer.type in normal_layers:
                layer.set_weights([initial_weights[layer_counter]])
                layer_counter += 1
        
        return model