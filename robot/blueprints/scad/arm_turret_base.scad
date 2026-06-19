// Arm turret: base yaw servo housed in a deck-bolted drum, horn disc
// on top carries the shoulder assembly. A ring of nylon washers
// between drum lip and disc takes the side loads, not the servo shaft.
include <servo_common.scad>

module arm_turret_base() {
    difference() {
        union() {
            rounded_plate(80, 80, 6, 8);
            cylinder(d = 62, h = 38);
        }
        translate([0, 0, 38]) servo_pocket(32);
        four_holes(66, 66, m4, 6);
    }
}
module turret_disc() {
    difference() {
        cylinder(d = 60, h = 6);
        horn_holes(6);
        four_holes(40, 40, m3, 6);   // shoulder bracket bolts here
    }
}
arm_turret_base();
translate([90, 0, 0]) turret_disc();
