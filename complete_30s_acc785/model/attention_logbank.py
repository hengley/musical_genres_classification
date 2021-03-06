# -*- coding: utf-8 -*-
# @Time    : 2019/2/4 18:03
# @Author  : shaoeric
# @Email   : shaoeric@foxmail.com

#
from keras.layers import  Input, AveragePooling1D, BatchNormalization, Dense, Flatten, Dropout, Conv2D, MaxPooling2D,GaussianNoise, CuDNNGRU, GlobalAveragePooling2D, Reshape
from keras.models import Model
from keras.constraints import maxnorm
import numpy as np
from sklearn.model_selection import train_test_split
from keras.utils.np_utils import to_categorical
from os import environ
from keras import optimizers,regularizers
from complete_30s_acc785.model.utils import *
from complete_30s_acc785.model.Attention import Attention

environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
environ["CUDA_VISIBLE_DEVICES"] = "0"

"""
[1.5282578134536744, 0.7]  未标准化2d卷积
[1.2823101806640624, 0.655] 未标准化的gru，虽然效果不错，但是训练时验证集效果波动太大，
[1.727592430114746, 0.705] 标准化2d卷积
[1.6496385669708251, 0.73] 未标准化 attention gru
"""

X = np.load('../features/concat_logbank.npy')
y = np.load('../features/target.npy')
y = to_categorical(y, 10)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=43, test_size=0.2)

def get_model():
    regularize = 0.01
    input_layer = Input(shape=(1, 1197, 120), name='attention_logbank_input')
    x = GaussianNoise(0.01)(input_layer)
    x = Conv2D(data_format='channels_first', filters=16, kernel_size=3, padding='same', activation='relu', kernel_initializer='glorot_normal', kernel_regularizer=regularizers.l2(regularize))(x)
    x = MaxPooling2D(pool_size=(3, 1), padding='valid', data_format='channels_first')(x)
    x = BatchNormalization()(x)
    x = Conv2D(filters=32, kernel_size=3, padding='same', activation='relu',kernel_initializer='glorot_normal', kernel_regularizer=regularizers.l2(regularize),data_format='channels_first')(x)
    x = MaxPooling2D(pool_size=(3, 1), padding='same', data_format='channels_first')(x)
    x = BatchNormalization()(x)
    x = Conv2D(filters=64, kernel_size=3, padding='same', activation='relu', kernel_initializer='glorot_normal', kernel_regularizer=regularizers.l2(regularize), data_format='channels_first')(x)
    x = MaxPooling2D(pool_size=2, padding='same', data_format='channels_first')(x)
    x = BatchNormalization()(x)
    x = Conv2D(filters=32, kernel_size=3, padding='same', activation='relu', kernel_initializer='glorot_normal', kernel_regularizer=regularizers.l2(regularize), data_format='channels_first')(x)
    x = MaxPooling2D(pool_size=2, padding='same', data_format='channels_first')(x)
    x = BatchNormalization()(x)
    x = Conv2D(filters=32, kernel_size=3, padding='same', activation='relu', kernel_initializer='glorot_normal', kernel_regularizer=regularizers.l2(regularize), data_format='channels_first')(x)
    x = MaxPooling2D(pool_size=2, padding='same', data_format='channels_first')(x)
    x = BatchNormalization()(x)
    x = Reshape(target_shape=(17, 32*15))(x)
    x = Dropout(0.3)(x)
    x = CuDNNGRU(34, return_sequences=True)(x)
    x = Attention(x.shape[1], name='attention')(x)
    x = Dropout(0.3)(x)
    x = Dense(10, activation='softmax', name='attention_logbank_output', kernel_initializer='glorot_normal', kernel_regularizer=regularizers.l2(regularize))(x)
    model = Model(input=input_layer, output=x)
    print(model.summary())
    return model


def train_only_attention_logbank(model, weights, epoch, X_train_argued, y_train_argued):
    # 过拟合严重
    history = model.fit({'attention_logbank_input': X_train_argued}, {'attention_logbank_output': y_train_argued}, epochs=epoch, validation_split=0.2)
    model.save_weights(weights)
    return history


def train(model, weights, epoch):
    # 生成训练数据
    X_train_argued, y_train_argued = argument_data(X_train, y_train, 300, 400, 1197, 120)
    X_train_argued, y_train_argued = get_argument_data_2d(X_train_argued, y_train_argued)
    history = train_only_attention_logbank(model, weights, epoch, X_train_argued, y_train_argued)
    plot_curve(history)


model = get_model()
model.compile(optimizer=optimizers.sgd(lr=1e-4, decay=2e-5), loss='categorical_crossentropy', metrics=['accuracy'])

# train(model, '../weights/attention_logbank.hdf5', epoch=20)

model.load_weights('../weights/attention_logbank.hdf5')
print(model.evaluate(np.expand_dims(X_test,axis=1), y_test))
