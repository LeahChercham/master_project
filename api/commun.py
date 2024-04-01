from sklearn.preprocessing import MinMaxScaler


def preprocess_data(X):
    print(40*"_")
    print("Preprocessing data...")
    
    res = X.copy()
    
    res = scaling_dew(res)
    
    # res = # TODO: finish this function
    
    
    
    print("Preprocessing done...")
    print(40*"_")
    return res


def scaling_dew(X): #TODO: test if this works as expected
    res = X.copy()
    
    res = MinMaxScaler(feature_range=(0, 1)).fit_transform(res.values.reshape(-1, 1))
    return res


def separate_xy(df, target_column):
    # Split the data into features and target
    X = df.index
    y = df[[target_column]]

    return X, y




def split_data_time(X, y, train_size=0.7, val_size=0.15, day=None):
    if day == None:
        # Calculate the lengths for training and validation sets
        len_train = int(len(X) * train_size)
        len_val = int(len(X) * val_size)

        # Calculate the indices for splitting
        ind_train_end = len_train
        ind_val_end = ind_train_end + len_val

        # Split the data into training, validation, and test sets
        X_train = X[:ind_train_end]
        X_val = X[ind_train_end:ind_val_end]
        X_test = X[ind_val_end:]

        # Split the labels accordingly
        y_train = y[:ind_train_end]
        y_val = y[ind_train_end:ind_val_end]
        y_test = y[ind_val_end:]

        return X_train, X_val, X_test, y_train, y_val, y_test
    
    else:
        # Find the index corresponding to the start of the specific day (00:00 timestamp) #TODO: verify if this works
        day_index = X.index[X.index.date == day.date()][0]

        # Split the data into training and test sets based on the specific date
        X_train = X[:day_index]
        X_test = X[day_index:]

        # Split the labels accordingly
        y_train = y[:day_index]
        y_test = y[day_index:]

        # No validation set for this case
        X_val, y_val = None, None
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
