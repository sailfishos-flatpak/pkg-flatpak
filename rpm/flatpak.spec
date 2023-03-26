%global bubblewrap_version 0.5.0
%global ostree_version 2020.8

Name:           flatpak
Version:        1.14.4
Release:        1%{?dist}
Summary:        Application deployment framework for desktop apps

License:        LGPLv2+
URL:            http://flatpak.org/
Source0:        %{name}-%{version}.tar.bz2
Source1:        pyparsing.py

BuildRequires: autoconf
BuildRequires: automake
BuildRequires: libtool
BuildRequires:  pkgconfig(appstream-glib)
BuildRequires:  pkgconfig(appstream)
BuildRequires:  pkgconfig(dconf)
BuildRequires:  pkgconfig(fuse)
BuildRequires:  gdk-pixbuf
BuildRequires:  pkgconfig(gio-unix-2.0)
BuildRequires:  pkgconfig(gobject-introspection-1.0) >= 1.40.0
BuildRequires:  pkgconfig(json-glib-1.0)
BuildRequires:  pkgconfig(libarchive) >= 2.8.0
BuildRequires:  pkgconfig(libseccomp)
BuildRequires:  pkgconfig(libsoup-2.4)
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  pkgconfig(libxml-2.0) >= 2.4
BuildRequires:  libzstd-devel >= 0.8.1
BuildRequires:  pkgconfig(ostree-1) >= %{ostree_version}
BuildRequires:  pkgconfig(polkit-gobject-1)
BuildRequires:  pkgconfig(libcurl)
BuildRequires:  bison
BuildRequires:  gettext
BuildRequires:  gpgme-devel
BuildRequires:  libcap-devel
#BuildRequires:  python3-pyparsing
BuildRequires:  systemd
BuildRequires:  xdg-dbus-proxy

%{?systemd_requires}

Requires:       librsvg%{?_isa}
Requires:       ostree-libs%{?_isa} >= %{ostree_version}
Requires:       /usr/bin/xdg-dbus-proxy
Requires:       %{name}-session-helper%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Recommends:     p11-kit-server

# comment out to break cycle
Requires:       xdg-desktop-portal > 0.10

%description
flatpak is a system for building, distributing and running sandboxed desktop
applications on Linux. See https://wiki.gnome.org/Projects/SandboxedApps for
more information.

%package devel
Summary:        Development files for %{name}
License:        LGPLv2+
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

%description devel
This package contains the pkg-config file and development headers for %{name}.

%package libs
Summary:        Libraries for %{name}
License:        LGPLv2+
Requires:       ostree%{?_isa} >= %{ostree_version}
Requires(pre):  /usr/sbin/useradd

%description libs
This package contains libflatpak.

%package session-helper
Summary:        User D-Bus service used by %{name} and others
License:        LGPLv2+
Conflicts:      flatpak < 1.4.1-2
Requires:       systemd

%description session-helper
This package contains the org.freedesktop.Flatpak user D-Bus service
that's used by %{name} and other packages.

%package tests
Summary:        Tests for %{name}
License:        LGPLv2+
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
Requires:       %{name}-session-helper%{?_isa} = %{version}-%{release}
Requires:       ostree%{?_isa} >= %{ostree_version}

%description tests
This package contains installed tests for %{name}.

# extra variables
%{!?_pkgdocdir: %global _pkgdocdir %{_docdir}/%{name}-%{version}}


%prep
%setup -q -n %{name}-%{version}/flatpak

cp %{SOURCE1} subprojects/variant-schema-compiler/

%build

# Fix generic python shebangs.
find tests -name '*.py' -exec \
    sed -i -e 's|/usr/bin/python|/usr/bin/python3|' {} +

(if ! test -x configure; then NOCONFIGURE=1 ./autogen.sh; CONFIGFLAGS=--disable-gtk-doc; fi;
 # Generate consistent IDs between runs to avoid multilib problems.
 export XMLTO_FLAGS="--stringparam generate.consistent.ids=1"
 %configure \
            --disable-docbook-docs \
            --enable-installed-tests \
            --disable-selinux-module \
            --with-priv-mode=none \
            --with-system-dbus-proxy \
            --disable-xauth \
            --disable-documentation \
            $CONFIGFLAGS)
%make_build V=1


%install
%make_install
install -d %{buildroot}%{_localstatedir}/lib/flatpak
install -d %{buildroot}%{_sysconfdir}/flatpak/remotes.d
rm -f %{buildroot}%{_libdir}/libflatpak.la
%find_lang %{name}

# remove generators as they confuse SFOS
rm -f %{buildroot}%{_prefix}/lib/systemd/system-environment-generators/60-flatpak-system-only
rm -f %{buildroot}%{_prefix}/lib/systemd/user-environment-generators/60-flatpak

%pre
getent group flatpak >/dev/null || groupadd -r flatpak
getent passwd flatpak >/dev/null || \
    useradd -r -g flatpak -d / -s /sbin/nologin \
     -c "User for flatpak system helper" flatpak
exit 0


%post -n flatpak-libs -p /sbin/ldconfig

%postun -n flatpak-libs -p /sbin/ldconfig

%files -f %{name}.lang
%license COPYING
%doc NEWS README.md
%{_bindir}/flatpak
%{_bindir}/flatpak-bisect
%{_bindir}/flatpak-coredumpctl
%{_datadir}/bash-completion
%{_datadir}/dbus-1/interfaces/org.freedesktop.portal.Flatpak.xml
%{_datadir}/dbus-1/interfaces/org.freedesktop.Flatpak.Authenticator.xml
%{_datadir}/dbus-1/services/org.flatpak.Authenticator.Oci.service
%{_datadir}/dbus-1/services/org.freedesktop.portal.Flatpak.service
%{_datadir}/dbus-1/system-services/org.freedesktop.Flatpak.SystemHelper.service
# Co-own directory.
#{_datadir}/gdm/env.d
%{_datadir}/fish/
%{_datadir}/%{name}
%{_datadir}/polkit-1/actions/org.freedesktop.Flatpak.policy
%{_datadir}/polkit-1/rules.d/org.freedesktop.Flatpak.rules
%{_datadir}/zsh/site-functions
%{_libexecdir}/flatpak-oci-authenticator
%attr(4755, root, root) %{_libexecdir}/flatpak-bwrap
%{_libexecdir}/flatpak-portal
%{_libexecdir}/flatpak-system-helper
%{_libexecdir}/flatpak-validate-icon
%{_libexecdir}/revokefs-fuse
%dir %{_localstatedir}/lib/flatpak
%{_sysconfdir}/dbus-1/system.d/org.freedesktop.Flatpak.SystemHelper.conf
%{_sysconfdir}/flatpak/remotes.d
%{_sysconfdir}/profile.d/flatpak.sh
%{_sysusersdir}/flatpak.conf
%{_unitdir}/flatpak-system-helper.service
%{_userunitdir}/flatpak-oci-authenticator.service
%{_userunitdir}/flatpak-portal.service
#{_prefix}/lib/systemd/system-environment-generators/60-flatpak-system-only
#{_prefix}/lib/systemd/user-environment-generators/60-flatpak

%files devel
%{_datadir}/gir-1.0/Flatpak-1.0.gir
%{_includedir}/%{name}/
%{_libdir}/libflatpak.so
%{_libdir}/pkgconfig/%{name}.pc

%files libs
%license COPYING
%{_libdir}/girepository-1.0/Flatpak-1.0.typelib
%{_libdir}/libflatpak.so.*

%files session-helper
%license COPYING
%{_datadir}/dbus-1/interfaces/org.freedesktop.Flatpak.xml
%{_datadir}/dbus-1/services/org.freedesktop.Flatpak.service
%{_libexecdir}/flatpak-session-helper
%{_userunitdir}/flatpak-session-helper.service

%files tests
%{_datadir}/installed-tests
%{_libexecdir}/installed-tests


%changelog
* Fri Dec 20 2019 David King <amigadave@amigadave.com> - 1.6.0-1
- Update to 1.6.0

* Mon Dec 16 2019 David King <amigadave@amigadave.com> - 1.5.2-1
- Update to 1.5.2

* Thu Nov 28 2019 David King <amigadave@amigadave.com> - 1.5.1-1
- Update to 1.5.1

* Fri Nov 01 2019 Orion Poplawski <orion@nwra.com> - 1.5.0-2
- Use %%{?selinux_requires} for proper install ordering

* Thu Oct 03 2019 David King <amigadave@amigadave.com> - 1.5.0-1
- Update to 1.5.0

* Thu Sep 19 2019 Kalev Lember <klember@redhat.com> - 1.4.3-1
- Update to 1.4.3

* Wed Sep 18 2019 Debarshi Ray <rishi@fedoraproject.org> - 1.4.2-6
- Trim unused shared library linkages from the session helper

* Wed Aug  7 2019 Owen Taylor <otaylor@redhat.com> - 1.4.2-5
- Add patch fixing problem with downloading icons for OCI remotes (#1683375)

* Thu Jul 25 2019 Tim Zabel <tjzabel21@gmail.com> - 1.4.2-4
- SELinux needs additional Requires (#1732132)

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.4.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Tue Jul 09 2019 Kalev Lember <klember@redhat.com> - 1.4.2-2
- Backport a patch that fixes a fairly large memory leak in gnome-software

* Fri Jun 28 2019 David King <amigadave@amigadave.com> - 1.4.2-1
- Update to 1.4.2 (#1725071)

* Tue Jun 25 2019 David King <amigadave@amigadave.com> - 1.4.1-3
- Use Requires(post) for selinux-policy (#1723118)

* Tue Jun 25 2019 Debarshi Ray <rishi@fedoraproject.org> - 1.4.1-2
- Split the session helper into a separate sub-package

* Thu Jun 13 2019 Kalev Lember <klember@redhat.com> - 1.4.1-1
- Update to 1.4.1

* Wed Jun 12 2019 Kalev Lember <klember@redhat.com> - 1.4.0-2
- Backport an upstream patch to fix gnome-software CI

* Tue May 28 2019 Kalev Lember <klember@redhat.com> - 1.4.0-1
- Update to 1.4.0

* Fri May 10 2019 Kalev Lember <klember@redhat.com> - 1.3.4-1
- Update to 1.3.4

* Tue Apr 30 2019 David King <amigadave@amigadave.com> - 1.3.3-2
- Generate consistent anchor IDs

* Fri Apr 26 2019 David King <amigadave@amigadave.com> - 1.3.3-1
- Update to 1.3.3 (#1699338)

* Wed Apr 17 2019 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 1.3.2-2
- Fixup selinux requires

* Fri Apr 12 2019 David King <amigadave@amigadave.com> - 1.3.2-1
- Update to 1.3.2 (#1699338)

* Wed Apr 03 2019 Kalev Lember <klember@redhat.com> - 1.3.1-2
- Add a oneshot systemd service to add Fedora flatpak repos
- Remove the post script to create system repo now that we have the service

* Wed Mar 27 2019 David King <amigadave@amigadave.com> - 1.3.1-1
- Update to 1.3.1 (#1693207)

* Tue Mar 12 2019 David King <amigadave@amigadave.com> - 1.3.0-1
- Update to 1.3.0

* Thu Feb 14 2019 David King <amigadave@amigadave.com> - 1.2.3-2
- Remove an obsolete Conflicts
- Use xdg-dbus-proxy

* Mon Feb 11 2019 David King <amigadave@amigadave.com> - 1.2.3-1
- Update to 1.2.3

* Wed Feb 06 2019 David King <amigadave@amigadave.com> - 1.2.2-1
- Update to 1.2.2

* Tue Feb 05 2019 Kalev Lember <klember@redhat.com> - 1.2.1-1
- Update to 1.2.1

* Mon Feb  4 2019 fedora-toolbox <otaylor@redhat.com> - 1.2.0-4
- Add an upstream patch to add flatpak build-export --disable-sandbox

* Thu Jan 31 2019 Bastien Nocera <bnocera@redhat.com> - 1.2.0-3
- Require librsvg2 so SVG icons can be exported

* Tue Jan 29 2019 Kalev Lember <klember@redhat.com> - 1.2.0-2
- Enable libsystemd support

* Mon Jan 28 2019 David King <amigadave@amigadave.com> - 1.2.0-1
- Update to 1.2.0

* Tue Jan 15 2019 Kalev Lember <klember@redhat.com> - 1.1.3-1
- Update to 1.1.3

* Fri Dec 21 2018 David King <amigadave@amigadave.com> - 1.1.2-1
- Update to 1.1.2

* Mon Dec 17 2018 David King <amigadave@amigadave.com> - 1.1.1-2
- Enable installed tests and add to tests subpackage

* Mon Dec 10 2018 Kalev Lember <klember@redhat.com> - 1.1.1-1
- Update to 1.1.1

* Fri Nov 30 2018 fedora-toolbox <otaylor@redhat.com> - 1.0.6-3
- Add a patch to fix OCI system remotes
- Add patch fixing permissions on icons downloaded from an OCI registry

* Fri Nov 16 2018 Kalev Lember <klember@redhat.com> - 1.0.6-1
- Update to 1.0.6

* Mon Nov 12 2018 Kalev Lember <klember@redhat.com> - 1.0.5-2
- Recommend p11-kit-server instead of just p11-kit (#1649049)

* Mon Nov 12 2018 Kalev Lember <klember@redhat.com> - 1.0.5-1
- Update to 1.0.5

* Fri Oct 12 2018 Kalev Lember <klember@redhat.com> - 1.0.4-1
- Update to 1.0.4

* Thu Oct 04 2018 Kalev Lember <klember@redhat.com> - 1.0.3-1
- Update to 1.0.3

* Thu Sep 13 2018 Kalev Lember <klember@redhat.com> - 1.0.2-1
- Update to 1.0.2

* Tue Aug 28 2018 David King <amigadave@amigadave.com> - 1.0.1-1
- Update to 1.0.1

* Mon Aug 20 2018 David King <amigadave@amigadave.com> - 1.0.0-2
- Fix double dash in XML documentation

* Mon Aug 20 2018 David King <amigadave@amigadave.com> - 1.0.0-1
- Update to 1.0.0

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.99.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Jul 10 2018 Kalev Lember <klember@redhat.com> - 0.99.3-1
- Update to 0.99.3

* Wed Jun 27 2018 Kalev Lember <klember@redhat.com> - 0.99.2-1
- Update to 0.99.2

* Thu Jun 21 2018 David King <amigadave@amigadave.com> - 0.99.1-1
- Update to 0.99.1

* Wed Jun 13 2018 David King <amigadave@amigadave.com> - 0.11.8.3-1
- Update to 0.11.8.3 (#1590808)

* Mon Jun 11 2018 David King <amigadave@amigadave.com> - 0.11.8.2-1
- Update to 0.11.8.2 (#1589810)

* Fri Jun 08 2018 David King <amigadave@amigadave.com> - 0.11.8.1-1
- Update to 0.11.8.1 (#1588868)

* Fri Jun 08 2018 David King <amigadave@amigadave.com> - 0.11.8-1
- Update to 0.11.8 (#1588868)

* Wed May 23 2018 Adam Jackson <ajax@redhat.com> - 0.11.7-2
- Remove Requires: kernel >= 4.0.4-202, which corresponds to rawhide
  somewhere before Fedora 22 which this spec file certainly no longer
  supports.

* Thu May 03 2018 Kalev Lember <klember@redhat.com> - 0.11.7-1
- Update to 0.11.7

* Wed May 02 2018 Kalev Lember <klember@redhat.com> - 0.11.6-1
- Update to 0.11.6

* Wed May 02 2018 Kalev Lember <klember@redhat.com> - 0.11.5-2
- Backport a fix for a gnome-software crash installing .flatpakref files

* Mon Apr 30 2018 David King <amigadave@amigadave.com> - 0.11.5-1
- Update to 0.11.5

* Thu Apr 26 2018 Kalev Lember <klember@redhat.com> - 0.11.4-1
- Update to 0.11.4

* Mon Feb 19 2018 David King <amigadave@amigadave.com> - 0.11.3-1
- Update to 0.11.3

* Mon Feb 19 2018 David King <amigadave@amigadave.com> - 0.11.2-1
- Update to 0.11.2

* Wed Feb 14 2018 David King <amigadave@amigadave.com> - 0.11.1-1
- Update to 0.11.1 (#1545224)

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.10.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Feb 02 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.10.3-2
- Switch to %%ldconfig_scriptlets

* Tue Jan 30 2018 Kalev Lember <klember@redhat.com> - 0.10.3-1
- Update to 0.10.3

* Thu Dec 21 2017 David King <amigadave@amigadave.com> - 0.10.2.1-1
- Update to 0.10.2.1

* Fri Dec 15 2017 Kalev Lember <klember@redhat.com> - 0.10.2-1
- Update to 0.10.2

* Fri Nov 24 2017 David King <amigadave@amigadave.com> - 0.10.1-1
- Update to 0.10.1

* Thu Oct 26 2017 Kalev Lember <klember@redhat.com> - 0.10.0-1
- Update to 0.10.0

* Mon Oct 09 2017 Kalev Lember <klember@redhat.com> - 0.9.99-1
- Update to 0.9.99

* Tue Sep 26 2017 Kalev Lember <klember@redhat.com> - 0.9.98.2-1
- Update to 0.9.98.2

* Tue Sep 26 2017 Kalev Lember <klember@redhat.com> - 0.9.98.1-1
- Update to 0.9.98.1

* Mon Sep 25 2017 Kalev Lember <klember@redhat.com> - 0.9.98-1
- Update to 0.9.98

* Thu Sep 14 2017 Kalev Lember <klember@redhat.com> - 0.9.12-1
- Update to 0.9.12

* Wed Sep 13 2017 Kalev Lember <klember@redhat.com> - 0.9.11-1
- Update to 0.9.11

* Mon Sep 04 2017 Kalev Lember <klember@redhat.com> - 0.9.10-1
- Update to 0.9.10
- Split out flatpak-builder to a separate source package

* Fri Aug 25 2017 Kalev Lember <klember@redhat.com> - 0.9.8-2
- Backport a patch to fix regression in --devel

* Mon Aug 21 2017 David King <amigadave@amigadave.com> - 0.9.8-1
- Update to 0.9.8

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.9.7-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Sun Jul 30 2017 Florian Weimer <fweimer@redhat.com> - 0.9.7-4
- Rebuild with binutils fix for ppc64le (#1475636)

* Thu Jul 27 2017 Owen Taylor <otaylor@redhat.com> - 0.9.7-3
- Add a patch to fix OCI refname annotation

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.9.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sat Jul 01 2017 David King <amigadave@amigadave.com> - 0.9.7-1
- Update to 0.9.7 (#1466970)

* Tue Jun 20 2017 David King <amigadave@amigadave.com> - 0.9.6-1
- Update to 0.9.6

* Sat Jun 10 2017 David King <amigadave@amigadave.com> - 0.9.5-1
- Update to 0.9.5 (#1460437)

* Tue May 23 2017 David King <amigadave@amigadave.com> - 0.9.4-1
- Update to 0.9.4 (#1454750)

* Mon Apr 24 2017 David King <amigadave@amigadave.com> - 0.9.3-1
- Update to 0.9.3

* Fri Apr 07 2017 David King <amigadave@amigadave.com> - 0.9.2-2
- Add eu-strip dependency for flatpak-builder

* Wed Apr 05 2017 Kalev Lember <klember@redhat.com> - 0.9.2-1
- Update to 0.9.2

* Wed Mar 15 2017 Kalev Lember <klember@redhat.com> - 0.9.1-1
- Update to 0.9.1

* Fri Mar 10 2017 Kalev Lember <klember@redhat.com> - 0.8.4-1
- Update to 0.8.4

* Sun Feb 19 2017 David King <amigadave@amigadave.com> - 0.8.3-3
- Make flatpak-builder require bzip2 (#1424857)

* Wed Feb 15 2017 Kalev Lember <klember@redhat.com> - 0.8.3-2
- Avoid pulling in all of ostree and only depend on ostree-libs subpackage

* Tue Feb 14 2017 Kalev Lember <klember@redhat.com> - 0.8.3-1
- Update to 0.8.3

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.8.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Jan 27 2017 Kalev Lember <klember@redhat.com> - 0.8.2-1
- Update to 0.8.2

* Wed Jan 18 2017 David King <amigadave@amigadave.com> - 0.8.1-1
- Update to 0.8.1

* Tue Dec 20 2016 Kalev Lember <klember@redhat.com> - 0.8.0-1
- Update to 0.8.0

* Tue Nov 29 2016 David King <amigadave@amigadave.com> - 0.6.14-2
- Add a patch to fix a GNOME Software crash
- Silence repository listing during post

* Tue Nov 29 2016 Kalev Lember <klember@redhat.com> - 0.6.14-1
- Update to 0.6.14

* Wed Oct 26 2016 David King <amigadave@amigadave.com> - 0.6.13-2
- Add empty /etc/flatpak/remotes.d

* Tue Oct 25 2016 David King <amigadave@amigadave.com> - 0.6.13-1
- Update to 0.6.13

* Thu Oct 06 2016 David King <amigadave@amigadave.com> - 0.6.12-1
- Update to 0.6.12

* Tue Sep 20 2016 Kalev Lember <klember@redhat.com> - 0.6.11-1
- Update to 0.6.11
- Set minimum ostree and bubblewrap versions

* Mon Sep 12 2016 David King <amigadave@amigadave.com> - 0.6.10-1
- Update to 0.6.10

* Tue Sep 06 2016 David King <amigadave@amigadave.com> - 0.6.9-2
- Look for bwrap in PATH

* Thu Aug 25 2016 David King <amigadave@amigadave.com> - 0.6.9-1
- Update to 0.6.9

* Mon Aug 01 2016 David King <amigadave@amigadave.com> - 0.6.8-1
- Update to 0.6.8 (#1361823)

* Thu Jul 21 2016 David King <amigadave@amigadave.com> - 0.6.7-2
- Use system bubblewrap

* Fri Jul 01 2016 David King <amigadave@amigadave.com> - 0.6.7-1
- Update to 0.6.7

* Thu Jun 23 2016 David King <amigadave@amigadave.com> - 0.6.6-1
- Update to 0.6.6

* Fri Jun 10 2016 David King <amigadave@amigadave.com> - 0.6.5-1
- Update to 0.6.5

* Wed Jun 01 2016 David King <amigadave@amigadave.com> - 0.6.4-1
- Update to 0.6.4

* Tue May 31 2016 David King <amigadave@amigadave.com> - 0.6.3-1
- Update to 0.6.3
- Move bwrap to main package

* Tue May 24 2016 David King <amigadave@amigadave.com> - 0.6.2-1
- Rename from xdg-app to flatpak (#1337434)
