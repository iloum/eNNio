
import scipy
from .video_modelling import video_modelling as vm
from .audio_modelling import audio_modelling as am
from .emotion_modelling import emotion_modelling as em
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

import re
import os

from sklearn.decomposition import PCA
from sklearn.cross_decomposition import CCA
from sklearn import manifold, datasets


def find_nearest(x,A,topk=1):
    '''
    returns the closest element in an array
    '''
    distances=np.linalg.norm(A-x,axis=1)
    sorted_idxes = np.argsort(distances)
    return sorted_idxes[:topk], distances[sorted_idxes[:topk]]

def parse_filename(filename):
    matched=re.match("(?:title_)?(.+)?-id_(.+)-specs_(.+)-from_([0-9]+)-to_([0-9]+)(\..+)?",filename)
    if matched:
        return matched.groups()
    else:
        return (filename,"","","","")


def get_inputs(loader,xdim_persample,features_number,target_video,inputs_path):
    datadict = loader.load_items(inputs_path)
    target_url = parse_filename(target_video)[1]
    proper_dict = {key:item for key,item in datadict.items() if parse_filename(Path(key).name)[1]!=target_url}
    #resize videos and exclude target video.
    proper_dict = {key:np.resize(item[0],(xdim_persample,features_number)) for key,item in proper_dict.items()}
    features_dict = {key:item[1] for key,item in datadict.items()}
    item_list = [item for key,item in proper_dict.items() if len(item)>0]
    item_list = np.array(item_list)

    return item_list, features_dict, [os.path.basename(x) for x in proper_dict.keys()]

def get_input(loader,xdim_persample,features_number,target_video):
        sample_video=loader.load_file(target_video)
        sample_video=np.resize(sample_video[0],(xdim_persample,features_number))
        return sample_video

def flatten(X):
    return X.reshape(X.shape[0],X.shape[1]*X.shape[2])

def collect_lists2set(lists):
    superset = set.union(*[set(listx) for listx in lists])
    return superset

def run_FFT(X):
    X = X.astype(float)
    X = np.abs(scipy.fft(X))**2
    return X[0:int(len(X)/2)]

def run_PCA(X):
    if X.shape[1]<2:
        return X, None
    pca = PCA()
    pca.fit(X)
    perc_ratio = (pca.explained_variance_ratio_[:-1]-pca.explained_variance_ratio_[1:])/pca.explained_variance_ratio_[:-1]
    perc_ratio_sudden_drop = [i+1 for i,x in enumerate(perc_ratio) if x<0.1 and i>=1]
    if perc_ratio_sudden_drop:
        n_components = perc_ratio_sudden_drop[0]+1
    else:
        return X, None
    pca2 = PCA(n_components=n_components)
    X_trans=pca2.fit_transform(X)
    return X_trans, pca2

def append_sample(x,y):
    return np.vstack((x,y[np.newaxis,:,:]))


def parse_videofeatures2segments(features):
    features = list(collect_lists2set(features.values()))

    colorsRGB = [i for i,x in enumerate(features) if re.match(r"Color-[RBG][0-9]+",x)]
    colorsSatur = [i for i,x in enumerate(features) if re.match(r"Color-Satur[0-9]+",x)]
    colorsGrey = [i for i,x in enumerate(features) if re.match(r"Color-Gray[0-9]+",x)]
    LBPs = [i for i,x in enumerate(features) if re.match(r"LBP",x)]
    Threshdolds = [i for i,x in enumerate(features) if re.match(r".*threshhold",x)]
    edges = [i for i,x in enumerate(features) if re.match(r"edges",x)]
    Sobel = [i for i,x in enumerate(features) if re.match(r".*[sS]obel",x)]
    flow = [i for i,x in enumerate(features) if re.match(r"^m|s$",x)]
    shots = [i for i,x in enumerate(features) if re.match(r"shots",x)]
    #restof = [x for x in range(X.shape[2]) if x not in subset_PCA]
    feature_segments=[colorsRGB,colorsSatur,colorsGrey,LBPs,Threshdolds,edges,Sobel,flow,shots]
    #for segment in feature_segments:
     #   print("----------")
      #  print(len(segment))
        #print([feature for i,feature in enumerate(features) if i in segment])
    return feature_segments


def parse_audiofeatures2segments(features):
    features = list(collect_lists2set(features.values()))

    mfcc_std = [i for i,x in enumerate(features) if re.match(r"mfcc_[0-9]+_std",x)]
    chroma_std = [i for i,x in enumerate(features) if re.match(r"chroma_[0-9]+_std",x)]
    zcr_mean = [i for i,x in enumerate(features) if re.match(r"zcr_mean",x)]
    spectral_entropy_mean = [i for i,x in enumerate(features) if re.match(r"spectral_entropy_mean",x)]
    spectral_centroid_std = [i for i,x in enumerate(features) if re.match(r"spectral_centroid_std",x)]
    energy_entropy_mean = [i for i,x in enumerate(features) if re.match(r"energy_entropy_mean",x)]
    chroma_mean = [i for i,x in enumerate(features) if re.match(r"chroma_[0-9]+_mean",x)]
    spectral_spread_std = [i for i,x in enumerate(features) if re.match(r"spectral_spread_std",x)]
    energy_std = [i for i,x in enumerate(features) if re.match(r"energy_std",x)]
    spectral_entropy_std = [i for i,x in enumerate(features) if re.match(r"spectral_entropy_std",x)]
    spectral_rolloff_mean = [i for i,x in enumerate(features) if re.match(r"spectral_rolloff_mean",x)]
    energy_mean = [i for i,x in enumerate(features) if re.match(r"energy_mean",x)]
    spectral_flux_std = [i for i,x in enumerate(features) if re.match(r"spectral_flux_std",x)]

    feature_segments=[mfcc_std,chroma_std,zcr_mean,spectral_entropy_mean,spectral_centroid_std, \
    energy_entropy_mean,chroma_mean,spectral_spread_std,energy_std,spectral_entropy_std,spectral_rolloff_mean, \
    energy_mean,spectral_flux_std]

    return feature_segments

def run_model(data):
    ILCond=min(data.shape[0], data.shape[1])
    n_components=2
    if ILCond<n_components:
        n_components = ILCond
    else:
        pass
    perplexities = [0.05,5, 30, 50, 70, 100]
    perplexity = perplexities[1]

    tsne = manifold.TSNE(n_components=n_components, init='random',early_exaggeration=250,learning_rate=100,
                         random_state=0, perplexity=perplexity,method="barnes_hut")
  
    return tsne.fit_transform(data)

def reduce_dimensions(X,subsets,precomputed_PCAs=[],run_TSNE=True):
    pca_list = []
    print("number of features before PCA:",X.shape[1]*X.shape[2])
    Xstar = np.take(X,subsets[0],axis=2)
    Xstar=np.apply_along_axis(run_FFT,1,Xstar)
    Xstar = flatten(Xstar)
    if not precomputed_PCAs:
        Xstar, pca_1 = run_PCA(Xstar)
        pca_list.append(pca_1)
    else:
        if precomputed_PCAs[0]:
            Xstar = precomputed_PCAs[0].transform(Xstar)
        else:
            pass
    for i,subset in enumerate(subsets[1:]):
        if subset:
            Xstarc = np.take(X,subset,axis=2)
            Xstarc=np.apply_along_axis(run_FFT,1,Xstarc)
            Xstarc = flatten(Xstarc)
            if not precomputed_PCAs:
                Xstarc, pca_x = run_PCA(Xstarc)
                pca_list.append(pca_x)
            else:
                if precomputed_PCAs[i+1]:
                    Xstarc = precomputed_PCAs[i+1].transform(Xstarc)
                else:
                    pass
            Xstar = np.hstack([Xstar,Xstarc])
    print("dimensionality reduction through PCA is complete, resulting number of features is:",Xstar.shape[1])
    if not precomputed_PCAs:
        if run_TSNE:
            TSNEd_data = run_model(Xstar)
            return TSNEd_data, pca_list
        else:
            return Xstar, pca_list
    else:
        if run_TSNE:
            TSNEd_data = run_model(Xstar)
            return TSNEd_data, precomputed_PCAs
        else:
            return Xstar, precomputed_PCAs


def plot_vectors(Y,labels,matches,predicted_path):
    _, ax = plt.subplots()
    ax.set_title("videomap")
    ax.scatter(Y[:-1, 0], Y[:-1, 1], c="r")
    ax.scatter(Y[-1, 0], Y[-1, 1], c="b")
    matches_coords=np.take(Y,matches,axis=0)
    ax.scatter(matches_coords[:,0],matches_coords[:,1],c="g")
    #ax.xaxis.set_major_formatter(NullFormatter())
    #ax.yaxis.set_major_formatter(NullFormatter())
    ax.axis('tight')

    for i, txt in enumerate(labels):
        ax.annotate(i, (Y[i, 0],  Y[i, 1]))
    predicted_title = parse_filename(os.path.basename(predicted_path))[0]
    ax.annotate(predicted_title, (Y[-1, 0],  Y[-1, 1]))
    plt.draw()

def get_video_identifier(filename):
    basename = str(os.path.basename(filename))
    parts=parse_filename(basename)
    #vid+from+to
    video_identifier = "_".join((parts[1],parts[3],parts[4]))
    return video_identifier

def align_videos(videos1,keys1,videos2,keys2):
    # need to get video identifiers...
    truekeys1 = [get_video_identifier(key) for key in keys1]
    truekeys2 = [get_video_identifier(key) for key in keys2]
    # find common keys
    common_keys = set(truekeys1).intersection(truekeys2)
    # sort keys based on video identifiers...
    pairs1 = [(keys1[i],i) for i,x in enumerate(truekeys1) if x in common_keys]
    pairs2 = [(keys2[i],i) for i,x in enumerate(truekeys2) if x in common_keys]
    pairs1.sort()
    pairs2.sort()
    # reaquire keys and videos correctly ordered...
    keys1 = [key for key,i in pairs1]
    keys2 = [key for key,i in pairs2]
    orderings1 = [i for key,i in pairs1]
    orderings2 = [i for key,i in pairs2]
    return videos1[orderings1], keys1, videos2[orderings2], keys2


def get_matches(Y,keys,video_root_path,audio_root_path,targetfilename,topk=5,export_locally=False):
    matches, distances = find_nearest(Y[-1],Y[:-1],topk=topk)
    probs = 1/distances/sum(1/distances)
    title = parse_filename(targetfilename)[0]
    for idx,match_idx in enumerate(matches):
        matched= list(keys)[match_idx]
        audio_path = Path(video_root_path,matched)
        audio_filename = matched.split(".")[0]
        parts = parse_filename(audio_filename)
        matched_audio_path=list(Path(audio_root_path).glob('*%s*%s*'%(parts[1],"from_"+parts[-3]+"-to_"+parts[-2])))[0]
        matched_video_path=list(Path(video_root_path).glob('*%s*%s*'%(parts[1],"from_"+parts[-3]+"-to_"+parts[-2])))[0]
        video_path = os.path.join(video_root_path,targetfilename)
        if export_locally:
            if matched_video_path and matched_audio_path:
                ffmpeg_com=f"""ffmpeg -y -t 60 -i {video_path} -i {matched_video_path} -i {matched_audio_path} \
                -filter_complex "[0:v]scale=256:144[v0];[1:v]scale=256:144[v1];[v1]drawtext='text={parts[0]}':fontcolor=white[v1b];[v0]drawtext='text={title}':fontcolor=white[v0b];[v0b][v1b]vstack[v]" \
                -map "[v]" -map 2:a -c:a aac -shortest -strict experimental recommendation_{idx}.mp4"""
                print(ffmpeg_com)
                os.system(ffmpeg_com)
            elif matched_audio_path:
                print("predict video clip is : ",matched)
                ffmpeg_com=f"ffmpeg -y -t 60 -i {video_path} -i {matched_audio_path} \
                -c:v copy -c:a aac -strict experimental recommendation_{idx}.mp4"
                print(ffmpeg_com)
                os.system(ffmpeg_com)
            else:
                print("could not fetch the audio/video")



    return matches,probs
