Name:           disk-analyzer
Version:        1.0
Release:        1%{?dist}
Summary:        Анализатор дискового пространства

License:        MIT
URL:            https://github.com/VinskiyL/DiskAnalyzer
Source0:        https://github.com/VinskiyL/DiskAnalyzer/releases/download/disk-analyzer/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
Requires:       python3-psutil
Requires:       python3-pyside6

%description
Графическое приложение для анализа использования дисков.

%prep
%setup -q -c

%build

%install
mkdir -p %{buildroot}/usr/lib/disk-analyzer
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/icons
mkdir -p %{buildroot}%{_datadir}/applications

install -m 644 *.py %{buildroot}/usr/lib/disk-analyzer/
install -m 755 disk-analyzer %{buildroot}%{_bindir}/
install -m 644 icons8-hdd-64.png %{buildroot}%{_datadir}/icons/disk-analyzer.png
install -m 644 DiskAnalyzer.desktop %{buildroot}%{_datadir}/applications/

%files
/usr/lib/disk-analyzer/
%{_bindir}/disk-analyzer
%{_datadir}/icons/disk-analyzer.png
%{_datadir}/applications/DiskAnalyzer.desktop

%changelog
* Tue Jul 15 2025 Чарушина Е.В. <katuhatm@gmail.com> - 1.0-1
- Первая версия пакета
