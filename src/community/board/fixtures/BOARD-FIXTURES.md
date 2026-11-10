# Board file-proof fixture provenance

The generated PDF/DOCX/CSV/ICS/WAV/text fixtures are constructed in proof.py and
contain imagined council-organising content. No member signatures or home data
are used.

`gps-camera-photo.jpg` is the original 640×480 Nikon camera JPEG from
[ianare/exif-samples, jpg/gps/DSCN0010.jpg](https://github.com/ianare/exif-samples/blob/master/jpg/gps/DSCN0010.jpg),
downloaded 26 October 2026. SHA256:
`17307b1207eb6487d7908e9d154890b46e3d2e0192369cfd3f4c33d5a5af4035`.
Original GPS IFD has ten tags, including latitude and longitude. The proof reads
those real tags but does not print their coordinates. This is a public test
photograph, not a photo of Seabright or a member's home. Upstream attribution and
licensing references remain with the sample collection; this copy is a testing
fixture, not board content or a product illustration.

`gps-photo.jpg` is Pillow's tiny malformed-GPS edge fixture,
[Pillow 12.3.0 Tests/images/exif_gps.jpg](https://github.com/python-pillow/Pillow/blob/12.3.0/Tests/images/exif_gps.jpg).
SHA256: `360eb3ce66533146584aa66576130c5ab98c763b7c7f51898892e7eaa7dcab49`.
It exercises malformed GPS stripping in addition to the actual camera photo;
it is not the evidence for the real-photograph requirement. Pillow source and
test licensing: [Pillow LICENSE](https://github.com/python-pillow/Pillow/blob/12.3.0/LICENSE).
