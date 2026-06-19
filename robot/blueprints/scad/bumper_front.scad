// Front bumper. Curved strip with two microswitch pockets so contact
// is a backup to the camera and cliff sensors. The slotted tabs give
// a few millimetres of float to press the switches. PETG works; TPU
// is even better. Print lying on its back face.

include <common.scad>

bump_w = 196;
bump_h = 26;
bump_t = 5;
arc_r = 320;

module bumper_front() {
    difference() {
        // Curved face
        intersection() {
            translate([0, -arc_r + 14, 0])
                linear_extrude(bump_h)
                    difference() {
                        circle(r = arc_r);
                        circle(r = arc_r - bump_t);
                    }
            translate([0, 0, bump_h / 2]) cube([bump_w, 40, bump_h], center = true);
        }
        // Microswitch lever windows
        for (x = [-50, 50])
            translate([x, 12, bump_h / 2])
                rotate([90, 0, 0]) slot(6, 14, 20);
    }
    // Mount tabs with float slots
    for (x = [-70, 0, 70])
        translate([x, 2, 0])
            difference() {
                rounded_plate(24, 26, 4, 3);
                slot(m3, 8, 4);
            }
}

bumper_front();
