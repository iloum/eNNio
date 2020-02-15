from ml_core.ml_model import MLModel
import pickle

from .coreml_TSNE.video_modelling import video_modelling as vm
from .coreml_TSNE.audio_modelling import audio_modelling as am
from .coreml_TSNE.emotion_modelling import emotion_modelling as em
import os
from .coreml_TSNE.utils import *

#metadata_columns = ['Title', 'Url', 'Video file path', 'Audio file path', 'Mismatch Title', 'Mismatch URL']


class TSNE(MLModel):
    def __init__(self, name):
       

        super().__init__(name)
        pass

    def train_ml_model(self, video_df, audio_df, m_df,drop=True):
        root_parsed = "data/downloads/parsed/"
        video_path = os.path.join(root_parsed,"video")
        audio_path = os.path.join(root_parsed,"audio")
        generated_dicts_path = "data/models/TSNE/"
        if drop:
            try:
                vm.drop_items(generated_dicts_path)
            except:
                pass
            vm.update_items(video_path,generated_dicts_path)

            try:
                am.drop_items(generated_dicts_path)
            except:
                pass
            am.update_items(audio_path,generated_dicts_path)

            try:
                em.drop_items(generated_dicts_path)
            except:
                pass
            em.update_items(video_path,generated_dicts_path)
        else:
            pass

        #ideally you need to exclude the target video from the list 
        #here we just drop a random video... to get things rolling..
        predicted_path = os.listdir(video_path)[0]
        # find the number of samples and features
        steps = 200
        video_features = 291
        audio_features = 136
        emotion_features=1
        Xemotion,emotionfeatures,emotionkeys = get_inputs(em,steps,emotion_features,predicted_path,generated_dicts_path)
        Xvideo, videofeatures, videokeys = get_inputs(vm,steps,video_features,predicted_path,generated_dicts_path)
        
        #align emotion and video features. takes care of file ordering, missing keys etc...
        Xvideo,videokeys,Xemotion,emotionkeys = align_videos(Xvideo,videokeys,Xemotion,emotionkeys)
        #concatenate video and emotion in one tensor/vector...
        Xvideo = np.concatenate((Xvideo,Xemotion),axis=2)

        #increment features by the number of emotion features..
        video_features +=emotion_features
        
        Xaudio, audiofeatures, audiokeys = get_inputs(am,steps,audio_features,predicted_path,generated_dicts_path)
        Xvideo,videokeys,Xaudio,audiokeys = align_videos(Xvideo,videokeys,Xaudio,audiokeys)


        videofeature_segments = parse_videofeatures2segments(videofeatures)
        audiofeature_segments = parse_audiofeatures2segments(audiofeatures)

        print("successfully trained the TSNE model")

        self.model = {
        "Xvideo":Xvideo, "Xaudio":Xaudio, "videofeatures":videofeatures,
        "videokeys":videokeys, "audiofeatures":audiofeatures, "audiokeys":audiokeys,
        "steps":steps

        }
        #pickle.dump(self.model, open(os.path.join(self._data_dir, self.name+".pkl"), "wb"))


        return self.model

    def evaluate_ml_model(self, video_df, audio_df, metadata_df):
       pass


    def predict_ml_model(self, video_df, audio_df, metadata_df, video_new,new_video_path):
        '''
        Method to predict based on input
        :param x_new: new unseen data
        :return: the predited value
        '''
        TSNE_model = self.model

        print("getting recommendations for {} please wait...".format(new_video_path))
     
        Xvideo,Xaudio,steps,videofeatures,audiofeatures,videokeys = TSNE_model["Xvideo"],TSNE_model["Xaudio"],TSNE_model["steps"],TSNE_model["videofeatures"],TSNE_model["audiofeatures"],TSNE_model["videokeys"]
        vmfeatures_number = [len(x) for x in videofeatures.values()][0]
        targetvideo_vm = get_input(vm,steps,vmfeatures_number,new_video_path)
        targetvideo_em = get_input(em,steps,1,new_video_path)
        targetvideo = np.concatenate((targetvideo_vm,targetvideo_em),axis=1)


        videofeature_segments = parse_videofeatures2segments(videofeatures)
        audiofeature_segments = parse_audiofeatures2segments(audiofeatures)

        Yvideo = reduce_dimensions(append_sample(Xvideo,targetvideo),videofeature_segments)
        Yaudio = reduce_dimensions(Xaudio,audiofeature_segments)

        Yvideo_subset = Yvideo[:-1,:]

        cca = CCA(n_components=2)
        cca.fit(Yvideo_subset, Yaudio)
        X_c, Y_c = cca.transform(Yvideo, Yaudio)
        
        video_root_path = "data/downloads/parsed/video"
        audio_root_path = "data/downloads/parsed/audio"
        matches,probs=get_matches(X_c,videokeys,video_root_path,audio_root_path,new_video_path,1)
        
        print("predicted probabilities and matched videos are:")
        for i,(prob,match_idx) in enumerate(zip(probs,matches)):
            matched= list(videokeys)[match_idx]
            title=matched
            print(title,"===>",prob)

        return metadata_df.index[metadata_df.Title==list(videokeys)[matches[0]]][0]

    def save_model(self, destination):
        """
        Method to save model
        Args:
            destination: Destination directory
        """
        with open(os.path.join(destination, self.name + ".dict"), "wb") as f:
            pickle.dump(self.model,f)
        
    def load_model(self, source):
        """
        Method to load saved model
        Args:
            source: Source directory
        """

        with open(os.path.join(source, self.name + ".dict"), "rb") as f:
            self.model=pickle.load(f)
            
