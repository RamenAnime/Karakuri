// Charging dock. Gentle ramp guides the robot until the underside
// contact shoe lands on two spring strips set in the recesses. An
// AprilTag plate stands at the back so SHIKAI can line up the
// approach. Dock electronics (LiFePO4 charger) sit behind the wall.
include <common.scad>

dock_w = 200; ramp_len = 110; land_len = 70; wall_h = 90;

module dock_base() {
    difference() {
        union() {
            // ramp
            hull() {
                translate([0, ramp_len / 2 + land_len / 2, 0])
                    linear_extrude(2) square([dock_w, ramp_len], center = true);
                translate([0, land_len / 2 - 4, 0])
                    linear_extrude(14) square([dock_w, 8], center = true);
            }
            // landing pad
            translate([0, 0, 0]) linear_extrude(14)
                square([dock_w, land_len], center = true);
            // back wall and tag plate
            translate([0, -land_len / 2 - 5, 0]) linear_extrude(wall_h)
                square([dock_w, 10], center = true);
        }
        // contact strip recesses, 60 mm apart
        for (x = [-30, 30])
            translate([x, 0, 14 - 3]) linear_extrude(4)
                square([14, 50], center = true);
        // strip screw holes
        for (x = [-30, 30], y = [-18, 18])
            translate([x, y, 0]) hole(m3, 14);
        // tag plate screw holes on the wall
        for (x = [-40, 40])
            translate([x, -land_len / 2 - 5, wall_h - 14])
                rotate([90, 0, 0]) translate([0, 0, -6]) cylinder(d = m3, h = 14);
        // cable exit
        translate([dock_w / 2 - 18, -land_len / 2 - 5, 6])
            rotate([90, 0, 0]) translate([0, 0, -6]) cylinder(d = 10, h = 14);
    }
}
dock_base();
