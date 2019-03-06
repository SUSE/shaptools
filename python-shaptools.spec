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


%{?!python_module:%define python_module() python-%{**} python3-%{**}}
Name:           python-shaptools
Version:        0.1.0
Release:        0
License:        GPL-2.0
Summary:        Python tools to interact with SAP HANA utilities
Url:            https://github.com/arbulu89/shaptools
Group:          Development/Languages/Python
Source:         shaptools-%{version}.tar.gz
BuildRequires:  python-rpm-macros
BuildRequires:  %{python_module devel}
BuildRequires:  %{python_module setuptools}
BuildRequires:  unzip
BuildRequires:  fdupes
BuildArch:      noarch

%ifpython2
Requires:  python-enum34
%endif

%python_subpackages

%description
API to expose SAP HANA functionalities

%prep
%setup -q -n shaptools-%{version}

%build
%python_build

%install
%python_install
%python_expand %fdupes %{buildroot}%{$python_sitelib}

%files %{python_files}
%doc CHANGELOG.md README.md
# %license macro is not availabe on older releases
%if 0%{?sle_version} <= 120300
%doc LICENSE
%else
%license LICENSE
%endif
%{python_sitelib}/*

%changelog
