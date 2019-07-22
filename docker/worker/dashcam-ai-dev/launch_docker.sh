#!/bin/bash
#
# $1 user unique dir
# $2 prefix
# $3 movie full filename
# $4 camera type
# $5 camera height (float)
# $6 movie start fno
# $7 movie end fno
#

# INPUT PARAMETERS:
#FILENAMES="/mnt/DENSO_DN-PROIII/Tei/20190224121442_0_0.mp4"

FILENAMES="/mnt/users/$1/$3"
PREFIX=$2
CAMERA="$4"
#CAMERA="KENWOOD_DRV-830_1920x1080_27fps"
#CAMERA="DENSO_DN-PROIII028_1920x1080_22fps"
#CAMERA_HEIGHT=1.0
CAMERA_HEIGHT=$5
START=$6
#START=0
END=$7
#END=1000

# MODEL PARAMETERS
MODEL0="allV2_and_lanes"
LABEL0="/mnt/models/allV2_and_lanes.pbtxt"
GRAPH0="/mnt/models/faster_rcnn_resnet50_lowproposals_train_allV2_and_lanes_v3-inference-336505.pb-frozen_inference_graph.pb"
# local path
CAMERA_JSON="${HOME}/feature-windows/tracking/settings/cameras.json"

BATCH_SIZE=20
THRESHOLD=0.5

for filename in ${FILENAMES}
do
    movie=`echo ${filename} | sed -e 's/.*\///g' -e 's/\.MOV//' -e 's/\.mov//' -e 's/\.avi//' -e 's/\.AVI//' -e 's/\.mp4//' -e 's/\.MP4//'`

    INPUT_MOVIE=${filename}
    OUTPUT_MOVIE="/mnt/users/$1/$2_labeled.mp4"

    #INPUT_JSON_FILENAME="/mnt/${movie}-resnet-allV2_and_lanes_v3_frozen_inference_graph-336505-nocropexpand-onlinetracking-pose-${THRESHOLD}.json"
    OUTPUT_JSON_FILENAME="/mnt/users/$1/$2.json"

    LOGFILE="/mnt/users/$1/$2.log"

    echo ${INPUT_MOVIE};
    echo ${OUTPUT_MOVIE};
    #echo ${INPUT_JSON_FILENAME};
    echo ${OUTPUT_JSON_FILENAME};
    echo ${LOGFILE};

    rm -fr ${OUTPUT_MOVIE}
    rm -fr ${OUTPUT_JSON_FILENAME};
    rm -fr /tmp/tracked.mp4
    rm -fr /tmp/tracked_distorted.mp4

    CUDA_VISIBLE_DEVICES=1 /usr/local/bin/trackingGlobalFullMatchTFClasses \
			--start=${START} \
			--end=${END} \
			--input_movie_filename=${INPUT_MOVIE} \
			--num_models=1 \
			--label0=${LABEL0} \
			--graph0=${GRAPH0} \
			--type0=resnet \
			--model0=${MODEL0} \
			--using_movie_input=true \
			--tepco=false \
			--warning_distance=500.0 \
			--camera_height=${CAMERA_HEIGHT} \
			--camera=${CAMERA} \
			--camera_json_filename=${CAMERA_JSON} \
			--crop_output=false \
			--expand_image_to_largest_dimension=false \
			--auto_crop=false \
			--batch_size=${BATCH_SIZE} \
			--output_movie_filename=${OUTPUT_MOVIE} \
			--threshold=${THRESHOLD} \
			--rectify=false \
			--use_precomputed_results=false \
			--save_detection_results=true \
			--output_json_filename=${OUTPUT_JSON_FILENAME} \
			--recompute_object_pose=true \
			--perform_online_tracking=true   > ${LOGFILE} 2>&1

    # bzip json
    #if [-e ${OUTPUT_JSON_FILENAME} ]; then
    #    echo "bzip json file..."
    #    bzip ${OUTPUT_JSON_FILENAME}
    #fi

    #mv /tmp/tracked.mp4             /tmp/${movie}-resnet-allV2_and_lanes_v3_frozen_inference_graph-336505-nocropexpand-onlinetracking-rectify-pose-${THRESHOLD}.tracked.mp4
    #mv /tmp/tracked_distorted.mp4   /tmp/${movie}-resnet-allV2_and_lanes_v3_frozen_inference_graph-336505-nocropexpand-onlinetracking-rectify-pose-${THRESHOLD}.tracked_distorted.mp4

done

#--input_json_filename=${INPUT_JSON_FILENAME} \
#--json_directory=${JSON_DIRECTORY} \
#--horizon=${HORIZON} \
#--centerfold=${CENTREFOLD} \



#for movie in "MinatoMirai_20180324_evening_830_I"	 "MinatoMirai_20180324_evening_830_J" 	 "MinatoMirai_20180324_evening_830_K" 	 "MinatoMirai_20180324_l_830_TEST" 	 "MinatoMirai_20180324_lunch_830_E" 	 "MinatoMirai_20180324_lunch_830_Ｆ" 	 "MinatoMirai_20180324_morning_830_A" 	 "MinatoMirai_20180331_E_830_TEST2" 	 "MinatoMirai_20180331_evening_830_O" 	 "MinatoMirai_20180331_evening_830_P" 	 "MinatoMirai_20180331_evening_830_Q" 	 "MinatoMirai_20180331_midnight_830_R" 	 "MinatoMirai_20180331_midnight_830_S" 	 "MinatoMirai_20180331_midnight_830_T" 	 "MinatoMirai_20180331_morning_830_L"   "MinatoMirai_20180331_morning_830_M";

#"20180826_112604_001_Camera1"  "20180826_125658_001_Camera1" 	     "20180826_125834_001_Camera1" 	     "20180826_134922_001_Camera1" 	     "20180826_152132_001_Camera1" 	     "20180826_162035_001_Camera1"
#for movie in "720_10_run_001_Camera1.avi"     "f_720p_30_run_001_Camera1.avi"  "f_720p_30_stop_001_Camera1.avi"
#for movie in "2019-02-12-08-37-49-Cam1.avi"
#for movie in "MinatoMirai_20180331_morning_830_L" "MinatoMirai_20180324_lunch_830_Ｇ"
#for movie in "MinatoMirai_20180331_morning_830_L"
#for movie in `find /mnt/KENWOOD-test-data/ | grep \.MOV | sed -e 's/.*\///g' -e 's/\.MOV//'`
#for movie in `find /mnt/shushudouga_maruyama/| grep -i \.MOV | sed -e 's/.*\///g' -e 's/\.MOV//' -e 's/\.mov//'`

#INPUT_MOVIE="/mnt/KENWOOD-test-data/${movie}.MOV";
#INPUT_MOVIE="/mnt/shushudouga_maruyama/${movie}.mov";
#INPUT_MOVIE=`ls /mnt/${movie}.mov | head -1`;
#INPUT_MOVIE=`ls /mnt/JupiterCameraVideosByMaruyama/${movie}.avi | head -1`;
#INPUT_MOVIE=`ls /mnt/genuine720p/${movie} | head -1`;
#INPUT_MOVIE=`ls /mnt/${movie} | head -1`;
#OUTPUT_MOVIE="/mnt/${movie}-resnet-vehicles_and_person_v6_frozen_inference_graph-200000-nocropexpand-onlinetracking-${THRESHOLD}.mp4"
#LOGFILE="/mnt/${movie}-resnet-vehicles_and_person_v6_frozen_inference_graph-200000-nocropexpand-onlinetracking-${THRESHOLD}.log"
#JSON_DIRECTORY="/mnt/${movie}-resnet-vehicles_and_person_v6_frozen_inference_graph-200000-nocropexpand-onlinetracking-${THRESHOLD}-json"


# TEMP HACK!
#INPUT_JSON_FILENAME="/mnt/${movie}-resnet-allV2_and_lanes_v3_frozen_inference_graph-336505-nocropexpand-onlinetracking-pose-${THRESHOLD}.recomputed.json.final"
#OUTPUT_JSON_FILENAME="/mnt/${movie}-resnet-allV2_and_lanes_v3_frozen_inference_graph-336505-nocropexpand-onlinetracking-pose-${THRESHOLD}.recomputed.json.ignore"


exit
