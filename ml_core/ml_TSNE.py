from ml_core.ml_model import MLModel
import pickle

from .coreml_TSNE.video_modelling import video_modelling as vm
from .coreml_TSNE.audio_modelling import audio_modelling as am
from .coreml_TSNE.emotion_modelling import emotion_modelling as em
import os
from .coreml_TSNE.utils import *



class TSNE(MLModel):
    def __init__(self, name):
       

        super().__init__(name)
        pass

    def train_ml_model(self, video_df, audio_df, m_df,drop=False,root_parsed="data/downloads/parsed/",generated_dicts_path="data/models/TSNE"):
        video_path = os.path.join(root_parsed,"video")
        audio_path = os.path.join(root_parsed,"audio")
        if drop:
            try:
                vm.drop_items(generated_dicts_path)
            except:
                pass

            try:
                am.drop_items(generated_dicts_path)
            except:
                pass
            

            try:
                em.drop_items(generated_dicts_path)
            except:
                pass
            
        #updates for new items. It skips previously added items.
        vm.update_items(video_path,generated_dicts_path)
        am.update_items(audio_path,generated_dicts_path)
        em.update_items(video_path,generated_dicts_path)


        #ideally you need to exclude the target video from the list 
        #here we just drop a random video... to get things rolling..
        predicted_path = os.listdir(video_path)[0]
        
        #hard constrains for Ennio 1.0 on fail assert, raise exception.
        steps = 200
        video_features = 289
        audio_features = 136
        emotion_features=1

        #get emotion features.
        Xemotion, _, emotionkeys = get_inputs(em,steps,emotion_features,predicted_path,generated_dicts_path)
        #get video features.
        Xvideo, videofeatures, videokeys = get_inputs(vm,steps,video_features,predicted_path,generated_dicts_path)
        
        #Since [] are returned, order might be random. Align video/audio correspondence.align emotion and video features. takes care of file ordering, missing keys etc...
        Xvideo,videokeys,Xemotion,emotionkeys = align_videos(Xvideo,videokeys,Xemotion,emotionkeys)
        #concatenate video and emotion in one tensor/vector...
        Xvideo = np.concatenate((Xvideo,Xemotion),axis=2)

        #increment features by the number of emotion features..
        video_features +=emotion_features
        
        #get audio features
        Xaudio, audiofeatures, audiokeys = get_inputs(am,steps,audio_features,predicted_path,generated_dicts_path)
        #Since [] are returned, order might be random. align video/audio correspondence. takes care of file ordering, missing keys etc...
        Xvideo,videokeys,Xemotion,emotionkeys = align_videos(Xvideo,videokeys,Xemotion,emotionkeys)
        Xvideo,videokeys,Xaudio,audiokeys = align_videos(Xvideo,videokeys,Xaudio,audiokeys)

        #parsed features to segments. E.g. All chroma together.
        videofeature_segments = parse_videofeatures2segments(videofeatures)
        audiofeature_segments = parse_audiofeatures2segments(audiofeatures)

        # run PCA on each segment e.g. One PCA for all chroma features.
        # TSNE is optional. TSNE has no predict method. 
        # skip it if you need to rerun it with new samples downstream.
        Yvideo, pca_transformations_video = reduce_dimensions(Xvideo,videofeature_segments,run_TSNE=False)
        Yaudio, pca_transformations_audio = reduce_dimensions(Xaudio,audiofeature_segments)


        print("successfully trained the TSNE model")

        self.model = {
        "Xvideo":Xvideo, "Xaudio":Xaudio, "videofeatures":videofeatures,
        "videokeys":videokeys, "audiofeatures":audiofeatures, "audiokeys":audiokeys,
        "steps":steps, "videofeature_segments":videofeature_segments, "audiofeature_segments":audiofeature_segments,
        "Yvideo":Yvideo,"Yaudio":Yaudio, "pca_transformations_video":pca_transformations_video, "pca_transformations_audio":pca_transformations_audio

        }


        return self.model

    def evaluate_ml_model(self, video_df, audio_df, metadata_df):
       pass


    def predict_ml_model(self, video_df, audio_df, metadata_df, video_new,new_video_path,video_root_path="data/downloads/parsed/video",audio_root_path="data/downloads/parsed/audio"):
        '''
        Method to predict based on input
        :param x_new: new unseen data
        :return: the predited value
        '''
        TSNE_model = self.model

        print("getting recommendations for {} please wait...".format(new_video_path))
     
        _,_,steps,videofeatures,_,videokeys = TSNE_model["Xvideo"],TSNE_model["Xaudio"],TSNE_model["steps"],TSNE_model["videofeatures"],TSNE_model["audiofeatures"],TSNE_model["videokeys"]
        
        #counts the number of video features
        vmfeatures_number = [len(x) for x in videofeatures.values()][0]\

        #get target video
        targetvideo_vm = get_input(vm,steps,vmfeatures_number,new_video_path)
        targetvideo_em = get_input(em,steps,1,new_video_path)
        targetvideo = np.concatenate((targetvideo_vm,targetvideo_em),axis=1)

        Yvideo,Yaudio = TSNE_model["Yvideo"], TSNE_model["Yaudio"]
        pca_transformations_video, _ = TSNE_model["pca_transformations_video"], TSNE_model["pca_transformations_audio"]
        videofeature_segments = TSNE_model["videofeature_segments"]

        #apply PCA for target video separately. Use the same transformations as in the training set. (Projects to new axis)
        target_videord,_ = reduce_dimensions(targetvideo[np.newaxis,:,:],videofeature_segments,pca_transformations_video,run_TSNE=False)
        Yvideo_plustarget = run_model(np.vstack((Yvideo,target_videord)))

        #run CCA with 2 components.
        cca = CCA(n_components=2)
        cca.fit(Yvideo_plustarget[:-1], Yaudio)
        X_c, _ = cca.transform(Yvideo_plustarget, Yaudio)
        
        #get matches
        matches,probs=get_matches(X_c,videokeys,video_root_path,audio_root_path,new_video_path,1)

        #print top ranked videos.
        print("predicted probabilities and matched videos are:")
        for _,(prob,match_idx) in enumerate(zip(probs,matches)):
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
            
