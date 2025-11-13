def update_workpiece_data(workpiece,contourObj,sprayContourObjs,sprayFillObjs,pickup_point):
    # ✅ Update the workpiece with transformed contours
    workpiece.contour = {"contour": contourObj.get(), "settings": {}}

    # Update workpiece spray contours correctly
    if sprayContourObjs is not None and "Contour" in workpiece.sprayPattern:
        for i, obj in enumerate(sprayContourObjs):
            if i < len(workpiece.sprayPattern["Contour"]):
                workpiece.sprayPattern["Contour"][i]["contour"] = obj.get()
    # Update workpiece spray fills correctly
    if sprayFillObjs is not None and "Fill" in workpiece.sprayPattern:
        for i, obj in enumerate(sprayFillObjs):
            if i < len(workpiece.sprayPattern["Fill"]):
                workpiece.sprayPattern["Fill"][i]["contour"] = obj.get()
    if pickup_point is not None:
        print(f"  📍 Original pickup point: ({workpiece.pickupPoint})")
        # Update workpiece with transformed pickup point
        workpiece.pickupPoint = f"{pickup_point[0]:.2f},{pickup_point[1]:.2f}"
        print(f"  📍 Transformed pickup point: ({pickup_point[0]:.1f}, {pickup_point[1]:.1f})")
