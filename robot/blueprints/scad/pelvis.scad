// Pelvis plate. Waist drum bolts on top centre; a biaxial hip joint
// hangs from the 50 mm square at each end. Battery straps run through
// the slots so the heaviest mass rides at the hips, where it belongs.
include <common.scad>

module pelvis() {
    difference() {
        rounded_plate(210, 110, 8, 10);
        four_holes(76, 76, m4, 8);                       // waist drum
        for (s = [-1, 1]) translate([s * 75, 0, 0]) four_holes(50, 50, m4, 8);  // hips
        for (s = [-1, 1]) translate([s * 35, 0, 0]) slot(4.5, 70, 8);           // battery straps
        for (s = [-1, 1]) translate([s * 75, 42, 0]) hole(12, 8);               // leg whip pass
    }
}
pelvis();
