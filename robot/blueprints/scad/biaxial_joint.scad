// Universal 2 axis joint, print 6 sets: shoulders (pitch+roll), hips
// (roll+pitch), ankles (pitch+roll). Piece A bolts to any 50 mm M4
// square and carries servo 1; piece B is the horn disc for servo 1 and
// carries servo 2 perpendicular; the next link bolts to servo 2's horn.
// Standard size servos throughout (DS3225 arms, DS5160 legs, same
// footprint). Both pieces flat, no supports.
include <servo_common.scad>

module biaxial_a() {
    difference() {
        union() {
            rounded_plate(64, 64, 7, 6);
            translate([0, 0, 7]) linear_extrude(30)
                offset(r=3) offset(delta=-3) square([servo_l + 12, servo_w + 12], center = true);
        }
        four_holes(50, 50, m4, 7);
        translate([0, 0, 37]) servo_pocket(30);
    }
}
module biaxial_b() {
    difference() {
        union() {
            cylinder(d = servo_horn_circle + 12, h = 7);
            translate([34, 0, 0]) linear_extrude(37)
                offset(r=3) offset(delta=-3) square([servo_w + 12, servo_l + 12], center = true);
            translate([10, -((servo_l+12)/2), 0]) cube([24, servo_l + 12, 7]);
        }
        horn_holes(7);
        translate([34, 0, 37]) rotate([0, 0, 90]) servo_pocket(30);
    }
}
biaxial_a(); translate([95, 0, 0]) biaxial_b();
