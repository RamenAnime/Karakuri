// Waist twist, +/-60 degrees. Scaled turret: drum on the pelvis, disc
// under the chest bottom ring. Nylon washers on the lip take the chest
// weight so the servo shaft only sees twist. Two pieces, flat.
include <servo_common.scad>

module waist_drum() {
    difference() {
        union() { rounded_plate(96, 96, 6, 8); cylinder(d = 80, h = 36); }
        translate([0, 0, 36]) servo_pocket(30);
        four_holes(76, 76, m4, 6);     // to pelvis
    }
}
module waist_disc() {
    difference() {
        cylinder(d = 78, h = 7);
        horn_holes(7);
        four_holes(50, 50, m4, 7);     // to chest bottom ring
    }
}
waist_drum(); translate([110, 0, 0]) waist_disc();
