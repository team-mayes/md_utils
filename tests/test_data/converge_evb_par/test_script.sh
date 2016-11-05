#!/usr/bin/env bash

#echo $val1
val_1=$(grep 'constant Vii' tests/test_data/converge_evb_par/evb_hm_maupin_gauss_3.5.par | awk '{print $1}')
val_2=$(grep 'Vij_const' tests/test_data/converge_evb_par/evb_hm_maupin_gauss_3.5.par | awk '{print $1}')
val_3=$(grep 'gamma' tests/test_data/converge_evb_par/evb_hm_maupin_gauss_3.5.par | awk '{print $1}')
if [ ${val_2} = "0.0" ]; then
    if [ ${val_1} = "-310.0" ]; then
        echo "3720.555681"
    elif [ ${val_1} = "-320.0" ]; then
        echo "3908.564528"
    elif [ ${val_1} = "-260.0" ]; then
        echo "4095.991942"
    elif [ ${val_1} = "-270.0" ]; then
        echo "4041.727547"
    elif [ ${val_1} == -300.0 ]; then
        echo "3595.483961"
    elif [ ${val_1} == -290.0 ]; then
        echo "3566.273748"
    elif [ ${val_1} == -280.0 ]; then
        echo "3738.904246"
    elif [ ${val_1} == -295.0 ]; then
        echo "3556.202196"
    elif [ ${val_1} == -292.5 ]; then
        echo "3553.132126"
    elif [ ${val_1} == -293.75 ]; then
        echo "3553.03728"
    elif [ ${val_1} == -293.125 ]; then
        echo "3552.909722"
    elif [ ${val_1} == -293.4375 ]; then
        echo "3552.909722"
    else
        echo "trouble"
    fi
elif [ ${val_2} = "-16.0" ]; then
    echo "2809.669242"
elif [ ${val_2} = "-32.0" ]; then
    echo "2075.995727"
elif [ ${val_2} = "-48.0" ]; then
    echo "2206.338675"
elif [ ${val_2} = "-40.0" ]; then
    echo "2134.748967"
elif [ ${val_2} = "-24.0" ]; then
    echo "2344.523372"
elif [ ${val_2} = "-36.0" ]; then
    echo "2102.873787"
elif [ ${val_2} = "-28.0" ]; then
    echo "2155.592724"
elif [ ${val_2} = "-34.0" ]; then
    echo "2087.055262"
elif [ ${val_2} = "-33.0" ]; then
    echo "2080.136096"
elif [ ${val_2} = "-30.0" ]; then
    echo "2092.608022"
elif [ ${val_2} = "-31.0" ]; then
    echo "2079.222656"
elif [ ${val_2} = "-31.5" ]; then
    echo "2076.278939"
elif [ ${val_2} = "-32.5" ]; then
    echo "2077.314211"
elif [ ${val_2} = "-31.75" ]; then
    if [ ${val_1} = "-293.4375" ]; then
        if [ ${val_3} = "0.0" ]; then
            echo "2075.873791"
        elif [ ${val_3} = "2.0" ]; then
            echo "2110.962464"
        elif [ ${val_3} = "-2.0" ]; then
            echo "9996209.35258"
        elif [ ${val_3} = "1.0" ]; then
            echo "2102.40171"
        elif [ ${val_3} = "-1.0" ]; then
            echo "99209.35258"
        elif [ ${val_3} = "0.5" ]; then
            echo "2099.941144"
        elif [ ${val_3} = "-0.5" ]; then
            echo "9209.35258"
        elif [ ${val_3} = "0.25" ]; then
            echo "2098.155013"
        fi
    elif [ ${val_1} = "-283.4375" ]; then
        echo "2015.04634"
    elif [ ${val_1} = "-273.4375" ]; then
        echo "2170.085425"
    elif [ ${val_1} = "-288.4375" ]; then
        echo "1993.584511"
    elif [ ${val_1} = "-285.9375" ]; then
        echo "1996.575003"
    elif [ ${val_1} = "-290.9375" ]; then
        echo "2014.530009"
    elif [ ${val_1} = "-287.1875" ]; then
        echo "1992.302255"
    elif [ ${val_1} = "-287.8125" ]; then
        echo "1992.393116"
    elif [ ${val_1} = "-286.5625" ]; then
        echo "1993.78691"
    elif [ ${val_1} = "-287.5" ]; then
        echo "1992.084732"
    elif [ ${val_1} = "-287.34375" ]; then
        echo "1992.155024"
    elif [ ${val_1} = "-287.65625" ]; then
        if  ${val_3} = "0.0" ]; then
            echo "1992.179245"
        fi
    fi
elif [ ${val_3} = "2.0" ]; then
    echo "2110.962464"
elif [ ${val_3} = "1.0" ]; then
    echo ""
else
    echo "more trouble"
fi
