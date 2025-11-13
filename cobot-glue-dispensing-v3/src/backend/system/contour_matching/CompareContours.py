import copy


from modules.shared.shared.ContourStandartized import Contour
from src.backend.system.contour_matching.alignment.contour_aligner import _alignContours
from src.backend.system.contour_matching.matching_config import *
from src.backend.system.contour_matching.similarity.geometric_matcher import _findMatches
from src.backend.system.contour_matching.similarity.ml_matcher import match_workpiece


def get_contour_objects(entries):
    objects = []
    for entry in entries:
        contour_data = entry.get("contour")
        if contour_data is not None:
            objects.append(Contour(contour_data))
    return objects

def prepare_data_for_alignment(matched):
    new_matched= []
    for match in matched:
        workpiece = copy.deepcopy(match["workpieces"])
        # ✅ Prepare main contour object
        main_contour = workpiece.get_main_contour()
        contourObj = Contour(main_contour)
        # ✅ Use the helper methods to get spray pattern data correctly
        sprayContourEntries = workpiece.get_spray_pattern_contours()
        sprayFillEntries = workpiece.get_spray_pattern_fills()
        # ✅ Create Contour objects for each spray pattern entry
        sprayContourObjs = get_contour_objects(sprayContourEntries)
        sprayFillObjs = get_contour_objects(sprayFillEntries)
        match["contourObj"] = contourObj
        match["sprayContourObjs"] = sprayContourObjs
        match["sprayFillObjs"] = sprayFillObjs
        new_matched.append(match)
    return new_matched

def findMatchingWorkpieces(workpieces, newContours):
    """
        Find matching workpieces based on new contours and align them.

        This function compares the contours of workpieces with the new contours and aligns them
        based on the similarity and defect thresholds.

        Args:
            workpieces (list): List of workpieces to compare against.
            newContours (list): List of new contours to be matched.

        Returns:
            tuple: A tuple containing:
                - finalMatches (list): List of workpieces that have been aligned and matched.
                - noMatches (list): List of contours that couldn't be matched.
                - newContoursWithMatches (list): List of new contours that have been matched.
        """
    print(f"🔍 ENTERING findMatchingWorkpieces with {len(workpieces)} workpieces and {len(newContours)} contours")
    """FIND MATCHES BETWEEN NEW CONTOURS AND WORKPIECES."""

    if USE_COMPARISON_MODEL:
        matched, noMatches, newContoursWithMatches = match_workpiece(workpieces,newContours)
    else:
        matched, noMatches, newContoursWithMatches = _findMatches(newContours,workpieces)


    """ALIGN MATCHED CONTOURS."""
    # prepare data for alignment
    new_matched = prepare_data_for_alignment(matched)



    finalMatches = _alignContours(new_matched, debug=DEBUG_ALIGN_CONTOURS)

    # print(f"Final Matched {len(finalMatches)} workpieces")
    return finalMatches, noMatches, newContoursWithMatches
    # return matched, noMatches, newContoursWithMatches







