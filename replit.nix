{pkgs}: {
  deps = [
    pkgs.libGL
    pkgs.ffmpeg
    pkgs.imagemagickBig
    pkgs.ffmpeg-full
    pkgs.postgresql
    pkgs.openssl
  ];
}
