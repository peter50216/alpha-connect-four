import json
import os
from random import sample

import numpy as np
from keras import Input, Model, regularizers
from keras.callbacks import EarlyStopping
from keras.layers import Dense, Conv3D, Flatten, AveragePooling3D, Maximum, Reshape, \
    RepeatVector, Permute, BatchNormalization, Activation, Add
from keras.optimizers import Adam

from state import State, FOUR, Action, Color, Augmentation

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))


def new_model_path():
    files = os.listdir(MODEL_DIR)
    model_files = [f for f in files if f.endswith('h5')]
    model_iteration = len(model_files)
    output_path = os.path.abspath(os.path.join(MODEL_DIR, '%6.6d.h5' % model_iteration))
    return output_path


def read_data(n_games, n_samples_per_game):
    files = os.listdir(DATA_DIR)
    game_names = list(sorted([f for f in files if f.endswith('.json')]))
    game_names = game_names[-n_games:]

    x = []
    y_policy = []
    y_reward = []

    for game_name in game_names:
        game_path = os.path.join(DATA_DIR, game_name)
        with open(game_path, 'r') as fin:
            game = json.load(fin)

        actions = [Action.from_hex(action_hex) for action_hex in game['actions']]
        states = []
        state = State.empty()
        for action in actions:
            state = state.take_action(action)
            states.append(state)
        states, final_state = states[:-1], states[-1]
        policies = game['policies']

        game_samples = sample(list(range(len(states))), 8)

        for augmentation, i in zip(Augmentation.iter_augmentations(), game_samples):
            state = states[i]
            sparse_policy = policies[i]

            x.append(state.to_numpy(augmentation))
            policy_index = sorted([(action.augment(augmentation).to_int(), action.to_hex())
                                   for action in Action.iter_actions()])
            y_policy.append([sparse_policy.get(action_hex, 0.0) for _, action_hex in policy_index])
            y_reward.append(_encode_winner(final_state.winner, state))

    return np.array(x), np.array(y_policy), np.array(y_reward)


def _encode_winner(winner: Color, state: State):
    if winner is state.next_color:
        return 1.0
    elif winner is state.next_color.other():
        return -1.0
    else:
        return 0.0


def create_model(input_size, filters, c=10 ** -4):
    l2 = regularizers.l2(c)
    input = Input(shape=(FOUR, FOUR, FOUR, input_size))
    input_conv = Conv3D(filters, 1, kernel_regularizer=l2)(input)
    pool1 = connect_layer(input_conv, filters, l2)
    pool2 = connect_layer(pool1, filters, l2)
    pool3 = connect_layer(pool2, filters, l2)
    pool4 = connect_layer(pool3, filters, l2)
    pool5 = connect_layer(pool4, filters, l2)

    collapse_action = Conv3D(2, (1, 1, 4), kernel_regularizer=l2)(pool5)
    norm_action = BatchNormalization()(collapse_action)
    activation_action = Activation('relu')(norm_action)
    flatten = Flatten()(activation_action)
    output_play = Dense(16, activation='softmax')(flatten)

    collapse_win = Conv3D(1, (1, 1, 4), kernel_regularizer=l2)(pool5)
    norm_win = BatchNormalization()(collapse_win)
    activation_win = Activation('relu')(norm_win)
    flatten_win = Flatten()(activation_win)
    dense_win = Dense(filters * 2, activation='relu', kernel_regularizer=l2)(flatten_win)
    output_win = Dense(1, activation='tanh', kernel_regularizer=l2)(dense_win)

    model = Model(inputs=input, outputs=[output_play, output_win])
    optimizer = Adam()
    metics = {'dense_1': 'categorical_accuracy', 'dense_3': 'mae'}
    model.compile(optimizer, ['categorical_crossentropy', 'mse'], metrics=metics)
    return model


def connect_layer(input, filters, l2):
    """Residual layer modeled after AlphaGo"""
    pool1 = line_convolution(input, filters, l2)
    norm1 = BatchNormalization()(pool1)
    relu1 = Activation('relu')(norm1)
    pool2 = line_convolution(relu1, filters, l2)
    norm2 = BatchNormalization()(pool2)
    add = Add()([input, norm2])
    relu2 = Activation('relu')(add)

    return relu2


def line_convolution(input, filters, l2):
    # todo add diagonal connection
    conv1 = Conv3D(filters, 1, kernel_regularizer=l2)(input)
    permute_x1 = pool_direction(conv1, filters, 0)
    permute_y1 = pool_direction(conv1, filters, 1)
    permute_z1 = pool_direction(conv1, filters, 2)
    pool1 = Maximum()([permute_x1, permute_y1, permute_z1])
    return pool1


def pool_direction(conv, filters, direction):
    pool_size = [1, 1, 1]
    pool_size[direction] = FOUR

    permute_dims = [1, 2, 3, 4]
    permute_dims.insert(0, permute_dims.pop(direction))

    pool = AveragePooling3D(pool_size, 1)(conv)
    gather = Reshape((FOUR * FOUR * filters,))(pool)
    repeat = RepeatVector(FOUR)(gather)
    spread = Reshape((FOUR, FOUR, FOUR, filters))(repeat)
    permute = Permute(permute_dims)(spread)
    return permute


if __name__ == '__main__':
    # todo move to argparse in __main__.py
    output_path = new_model_path()
    input_shape = State.empty().to_numpy().shape[-1]
    model = create_model(input_shape, filters=10)
    print(model.summary())

    x_state, y_policy, y_reward = read_data(1000, 3)
    model.fit(x_state, [y_policy, y_reward], epochs=100, validation_split=0.3,
              callbacks=[EarlyStopping(patience=2)])

    model.save(output_path)
