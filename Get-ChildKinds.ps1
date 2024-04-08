
function Get-KindAttributeOffset {
    param (
        [string]$DirectoryPath = $env:TEMP
    )
	
	$shell = New-Object -ComObject Shell.Application
	$folder = $shell.Namespace($DirectoryPath)
	
	# Ensure the directory exists
    if (-not (Test-Path $DirectoryPath)) {
        Write-Warning "Directory does not exist: $DirectoryPath"
		# Fallback to temp
        $DirectoryPath = $null
		if (Resolve-Path "$($env:TEMP)" -ErrorAction SilentlyContinue){
			$DirectoryPath = Resolve-Path "$($env:TEMP)"
	    } else {
			$DirectoryPath = Resolve-Path "$($env:TMP)" -ErrorAction Inquire
		}
    }
	
	# Use a known file extension to help identify the 'Kind' property index
	$tempFilePath = [System.IO.Path]::Combine($DirectoryPath, [System.Guid]::NewGuid().ToString() + ".txt")
	$tempFile = New-Item -ItemType File -Path $tempFilePath -Force
	Add-Content -Path $tempFilePath -Value "Temporary file for identifying 'Kind' property index."
	$tempItem = $folder.ParseName($tempFile.Name)

	# Initialize variable to hold the 'Kind' property index
	$kindPropertyIndex = $null

	# Try to find the 'Kind' property index
	foreach ($index in 0..300) {
		$propValue = $folder.GetDetailsOf($tempItem, $index)
		if ($propValue -eq "Document") {
			$kindPropertyIndex = $index
			break
		}
	}

	# Cleanup
	Remove-Item $tempFilePath -Force
	[System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell) | Out-Null
	
	# Return results
	if ($kindPropertyIndex -eq $null) {
		Write-Error "Failed to determine 'Kind' property index."
		return
	}
	return $kindPropertyIndex
}


function Get-ChildKinds {
    param (
        [string]$DirectoryPath,
        [string]$OutputType = "object"
    )

    # Create a Shell.Application object
    $shell = New-Object -ComObject Shell.Application

    # Ensure the directory exists
    if (-not (Test-Path $DirectoryPath)) {
        Write-Error "Directory does not exist: $DirectoryPath"
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell) | Out-Null
        return
    }

    # Get the folder object
    $folder = $shell.Namespace($DirectoryPath)
    $kindPropertyIndex = Get-KindAttributeOffset -DirectoryPath $DirectoryPath

    # Collect details for each item in the directory into an array of PSCustomObject
    $itemsDetails = foreach ($item in $folder.Items()) {
        [PSCustomObject]@{
            Kind = $folder.GetDetailsOf($item, $kindPropertyIndex)
            Type = $item.Type
            Path = $item.Path
        }
    }

    # Output the collection based on the requested output type
    $output = switch ($OutputType) {
        "json" { $itemsDetails | ConvertTo-Json }
        "xml" { $itemsDetails | ConvertTo-Xml -NoTypeInformation }
        "object" { $itemsDetails }
        default {
            Write-Error "Invalid output type: $OutputType"
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell) | Out-Null
            return
        }
    }

    # Release the COM object
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell) | Out-Null
	return $output
}