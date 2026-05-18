%% Auto-detect CarSim installation path
% Returns [csExe, csDir] — both empty if not found
function [csExe, csDir] = find_carsim()
    csExe = '';
    csDir = '';
    searchRoots = {'C:\Program Files (x86)'; 'C:\Program Files'};

    for r = 1:length(searchRoots)
        if ~exist(searchRoots{r}, 'dir')
            continue;
        end
        d = dir(fullfile(searchRoots{r}, 'CarSim*'));
        for i = 1:length(d)
            if ~d(i).isdir
                continue;
            end
            candidate = fullfile(searchRoots{r}, d(i).name, 'CarSim.exe');
            if exist(candidate, 'file')
                csExe = candidate;
                csDir = fullfile(searchRoots{r}, d(i).name);
            end
        end
    end
end
