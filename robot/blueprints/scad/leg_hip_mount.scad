// Hip mount: bolts a coxa servo vertically at a deck corner so its
// output shaft points down. Print 4. Flat side down, no supports.
include <servo_common.scad>

module leg_hip_mount() {
    difference() {
        union() {
            rounded_plate(64, 34, 6, 4);             // deck plate
            translate([0, 0, 6]) linear_extrude(30)   // servo box
                offset(r = 3) offset(delta = -3)
                    square([servo_l + 10, servo_w + 10], center = true);
        }
        translate([0, 0, 36]) servo_pocket(30);
        four_holes(54, 24, m4, 6);
    }
}
leg_hip_mount();
