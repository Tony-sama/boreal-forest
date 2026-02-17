import numpy as np
import itertools
import pandas as pd
from config import *
import pylfit

USE_NAN = True
HEURISTICS = ["try_all_atoms", "max_coverage_static"] #["max_coverage_static"] #["try_all_atoms", "max_coverage_dynamic", "max_coverage_static", "max_diversity"]

def generation_synthetique(df_X:pd.DataFrame, R, K, A, col_tmp, 
                           reverse_tmp=False, init=1, col_selection=None):
    R, K, A = np.asarray(R), np.asarray(K), np.asarray(A)
    
    ## Vérification des dimensions des matrices de paramètres
    shape_R, shape_K, shape_A = R.shape, K.shape, A.shape
    if not( (len(shape_R) == len(shape_K) == (len(shape_A)-1)) or (len(shape_R) == len(shape_K) == (len(shape_A)))) :
        raise ValueError(f"dimensions de R, K, A doivent être n, n, n+1 ou n. {len(shape_R)}, {len(shape_K)}, {len(shape_A)}")
    n = len(shape_R)
    if n>0:
        dims = np.array([shape_R, shape_K, shape_A[:n]])
        dim = dims.max(axis=0)
        if not ( (dims == 1) + (dims == dim[None,:])).all():
            ValueError(f"dimensions de R, K, A incohérentes : {shape_R}, {shape_K}, {shape_A}")
    else:
        dim = np.array((), dtype='int64')
    
    if n==len(shape_A):
        A = A[..., None]
        shape_A = A.shape


    if not col_tmp in df_X:
        ValueError(f"df_X ne contient pas col_tmp {col_tmp}")
    
    df_sorted = df_X.sort_values(col_tmp, ascending=not(reverse_tmp)).reset_index(drop=True)

    shape_X = df_sorted.shape
    if len(shape_X) != 2:
        ValueError(f"shape de df_X invalide : doit être (a, b). {shape_X}")
    
    N, p = shape_X
    if col_selection is None:
        col_selection = df_X.columns.drop(col_tmp)
    
    if len(col_selection) != shape_A[-1]:
        ValueError(f"dimensions de df_X et A incohérents : {col_tmp}")

    Synth = np.zeros((*dim,N))

    Synth[... ,0] = init  # condition initiale

    # intégration dans l'ordre des profondeurs décroissantes
    for i in range(1, N):
        Xt = Synth[...,i-1]
        X_others = df_sorted.loc[i-1, col_selection].values
        interaction = np.dot(A, X_others)
        dX = R*Xt*(1 - Xt/K) + Xt*interaction
        Synth[..., i] = np.maximum(0, Xt + dX)

    print(f"{dim} : {np.prod(dim)} espèces générées sur {N-1} intération{"s" if N-1>1 else ""}.")

    # ré-attacher la colonne Synth dans le df initial, réordonné comme avant
    for i_d in itertools.product(*[range(d) for d in dim]):
        col_name = "Synth" + "".join([f"_{j_d}" for j_d in i_d])
    
        df_sorted[col_name] = Synth[*i_d,:]

    if reverse_tmp:
        df_X_synth = df_sorted.sort_values(col_tmp, ascending=reverse_tmp).reset_index(drop=True)
    else:
        df_X_synth = df_sorted
    return df_X_synth



def supports(rules, dataset):
    """
    Extract feature state where each rule apply. Dataset must be same as the one that train the rules.
    """
    output = dict()

    for r in rules:
        supports = []
        for s1,s2 in dataset.data:
            if r.matches(s1) and r.head.matches(s2):
                supports += [(s1,s2)]
        output[r] = supports

    return output

def extract_influences(rules, dataset):
    rules_supports = supports(rules, dataset)

    data = []
    for r in rules:
        data.append([r.head.variable, r.head.value, len(rules_supports[r]), r, [(tuple(s1),tuple(s2)) for s1,s2 in rules_supports[r]], r.to_string()])
    
    df = pd.DataFrame(data, columns=["head_variable", "head_value", "nb_supports", "rule", "supports", "rule_str"])
    df_output = pd.DataFrame([], columns=["target", "feature", "positive_influence", "negative_influence", "influence"])

    for target,vals in dataset.targets:
        df_tmp = df[df["head_variable"] == target]
        influences = {}

        # Extract inhibitions
        df_0 = df_tmp[df_tmp["head_value"] == "-1"]

        for idx, row in df_0.iterrows():
            rule = row["rule"]

            for feature in rule.body:
                label = rule.body[feature].to_string()
                if label not in influences:
                    influences[label] = {"negative": 0, "positive":0}
                influences[label]["negative"] += row["nb_supports"] / rule.size()

        # Extract activations
        df_1 = df_tmp[df_tmp["head_value"] == "1"]

        for idx, row in df_1.iterrows():
            rule = row["rule"]

            for feature in rule.body:
                label = rule.body[feature].to_string()
                if label not in influences:
                    influences[label] = {"negative": 0, "positive":0}
                influences[label]["positive"] += row["nb_supports"] / rule.size()

        # Build output dataframe
        data = []
        for var in influences:
            data += [[target, var, influences[var]["positive"], influences[var]["negative"]]]

        df_tmp = pd.DataFrame(data, columns=["target", "feature", "positive_influence", "negative_influence"])
        df_tmp["influence"] = df_tmp["positive_influence"] - df_tmp["negative_influence"]
        df_tmp["influence"] = df_tmp["influence"].astype(int)
        df_output = pd.concat([df_output,df_tmp])

    df_output = df_output.sort_values(by=["influence"],ascending=False)
    
    return df_output



def analyse(FEATURES_ONLY, TARGETS_ALL, DISCRETE_DATA_PATH):
    l_influences = []

    df = pd.read_csv(DISCRETE_DATA_PATH)

        # Load training dataset
    cols = [c for c in df.columns if c not in list(df.select_dtypes(exclude=["number"]).columns)]
    df[cols] = df[cols].astype('Int64')
    df[cols] = df[cols].astype('string')

    if not USE_NAN:
        df = df.dropna()
    else:
        df = df.fillna("?")

    col_order = list(df.columns)

    df_output = pd.DataFrame(columns=["head_variable", "head_value", "nb_supports", "rule", "supports", "rule_str"])

    df.to_csv("tmp/lfit_input.csv")

    for i in range(len(TARGETS_ALL)):
        TARGETS = TARGETS_ALL[i:i+1]
        FEATURES = FEATURES_ONLY + TARGETS

        TARGETS = [c+"_change" for c in TARGETS]

        # Convert array data as a DiscreteStateTransitionsDataset using pylfit.preprocessing
        dataset = pylfit.preprocessing.discrete_state_transitions_dataset_from_csv(path="tmp/lfit_input.csv", \
        feature_names=FEATURES, target_names=TARGETS,unknown_values=["?"])

        # Initialize a DMVLP with the dataset variables and set GULA as learning algorithm
        model = pylfit.models.DMVLP(features=dataset.features, targets=dataset.targets)
        model.compile(algorithm="gula") # model.compile(algorithm="pride")
        model.fit(dataset=dataset, options={"heuristics":HEURISTICS, "verbose":1, 
                                            "threads":THREADS, "supported_only":True})

        df_influences = extract_influences(model.rules,dataset)
        l_influences.append(df_influences)
    return l_influences

    