// Head: pan base, tilt yoke, face plate. Pan +/-90, tilt -30 to +60 so
// the robot looks up at counters and down at the floor. Face plate has
// the 1/4-20 for an OAK-D Lite (the humanoid head camera; the Kinect is
// too wide and heavy for a neck) plus Pi camera slots. Three pieces on
// one plate, all flat, no supports.
include <servo_common.scad>

module pan_base() {           // bolts to chest top ring, pan servo inside
    difference() {
        union() { rounded_plate(70, 70, 6, 6); cylinder(d = 56, h = 32); }
        translate([0, 0, 32]) servo_pocket(28);
        four_holes(50, 50, m4, 6);
    }
}
module tilt_yoke() {          // horn disc below, two uprights carry tilt servo
    difference() {
        union() {
            cylinder(d = 44, h = 6);
            for (s = [-1, 1]) translate([s * 26, 0, 0])
                linear_extrude(58) translate([-s * 4, 0]) square([8, 36], center = true);
        }
        horn_holes(6);
        // tilt servo bolts through one upright
        translate([26, 0, 40]) rotate([0, 90, 0]) translate([0, 0, -10]) {
            cylinder(d = 12, h = 20);
            for (y = [-servo_tab_span / 2, servo_tab_span / 2])
                translate([0, y, 0]) rotate([0,0,0]) cylinder(d = servo_tab_hole, h = 20);
        }
        // bearing bolt through the other
        translate([-26, 0, 40]) rotate([0, 90, 0]) translate([0, 0, -10]) cylinder(d = m4, h = 20);
    }
}
module face_plate() {         // horn-mounts to the tilt axis, carries the camera
    difference() {
        rounded_plate(84, 64, 6, 6);
        translate([0, 0, 0]) hole(quarter_inch, 6);            // OAK-D Lite
        for (x = [-10.5, 10.5], y = [-16, 16]) translate([x, y, 0]) slot(2.4, 5, 6);  // Pi cam
        translate([-34, 0, 0]) horn_holes(6);                  // tilt horn
        translate([34, 0, 0]) hole(m4, 6);                     // idler bolt
    }
}
pan_base(); translate([95, 0, 0]) tilt_yoke(); translate([0, 95, 0]) face_plate();
