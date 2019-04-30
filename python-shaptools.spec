#
# spec file for package python-shaptools
#
# Copyright (c) 2019 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/

Name:           python-shaptools
Version:        0.1.0
Release:        0
License:        Apache-2.0
Summary:        Python tools to interact with SAP HANA utilities
Url:            https://github.com/SUSE/shaptools
Group:          Development/Languages/Python
Source:         shaptools-%{version}.tar.gz
BuildRequires:  python-devel python3-devel
BuildRequires:  python-setuptools python3-setuptools
BuildRequires:  fdupes
BuildArch:      noarch

%description
API to expose SAP HANA functionalities

%package -n python2-shaptools
Summary:        Python tools to interact with SAP HANA utilities (python2)
%{?python_provide:%python_provide python2-shaptools}

%description -n python2-shaptools
API to expose SAP HANA functionalities (python2)

%package -n python3-shaptools
Summary:        Python tools to interact with SAP HANA utilities (python3)
%{?python_provide:%python_provide python3-shaptools}

%description -n python3-shaptools
API to expose SAP HANA functionalities (python3)

%prep
%setup -q -n shaptools-%{version}

%build
python2 setup.py build --build-lib=py2/build/lib
python3 setup.py build --build-lib=py3/build/lib

%install
mv py2/build .
python2 setup.py install -O1 --skip-build --force --root %{buildroot} --prefix=%{_prefix}
%fdupes %{buildroot}%python_sitelib
rm -rf build
mv py3/build .
python3 setup.py install -O1 --skip-build --force --root %{buildroot} --prefix=%{_prefix}
%fdupes %{buildroot}%python3_sitelib

%files -n python2-shaptools
%doc CHANGELOG.md README.md
# %license macro is not available on older releases
%if 0%{?sle_version} <= 120300
%doc LICENSE
%else
%license LICENSE
%endif
%{python_sitelib}/*

%files -n python3-shaptools
%doc CHANGELOG.md README.md
# %license macro is not available on older releases
%if 0%{?sle_version} <= 120300
%doc LICENSE
%else
%license LICENSE
%endif
%{python3_sitelib}/*

%changelog
