(async function spotifyDL() {
  if (!Spicetify.React || !Spicetify.ReactDOM || !Spicetify.ContextMenu) {
    setTimeout(spotifyDL, 300);
    return;
  }

  const downloadButton = new Spicetify.ContextMenu.Item(
    "Download",
    async (uris) => {
      // Increment task count
      fetch(`http://localhost:5000/add/${uris.length}`, {
        method: "GET",
      });

      for (const uri of uris) {
        try {
          const [, elementType, elementId] = uri.split(":");
          const elementUrl = `https://api.spotify.com/v1/${elementType}s/${elementId}`;
          const elementData = await Spicetify.CosmosAsync.get(elementUrl);
          const elementName = elementData.name;

          let displayName;
          if (elementData.artists) {
            displayName = `${elementData.artists[0].name} - ${elementName}`;
          } else {
            displayName = elementName;
          }

          Spicetify.showNotification(
            `Downloading ${displayName}..`,
            false,
            3000
          );

          fetch(`http://localhost:5000/${elementType}/${elementId}`, {
            method: "GET",
          })
            .then((response) => {
              if (response.ok) {
                Spicetify.showNotification(
                  `Successfully downloaded ${displayName} !`,
                  false,
                  3000
                );
              } else {
                Spicetify.showNotification(
                  `Error ${response.status}`,
                  true,
                  3000
                );
              }
            })
            .catch((error) => {
              console.error(`Error during download: ${error}`);
              Spicetify.showNotification(
                `${error}. Make sure the SpotifyDL server is running.`,
                true,
                3000
              );
              return;
            });
        } catch (error) {
          console.error("Error during URI parsing:", error);
        }
      }
    },
    // If is track, album, playlist or artist
    (uris) => {
      if (!uris) return false;
      const validTypes = ["track", "album", "playlist", "artist"];
      return validTypes.some((type) => uris[0].includes(`spotify:${type}:`));
    },
    `<svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 12l-4-4h2.5V4h3v4H12l-4 4z"/><path d="M14 13v1H2v-1h12z"/></svg>`,
    false
  );

  const openInExplorerButton = new Spicetify.ContextMenu.Item(
    "Open in file explorer",
    async (uris) => {
      for (const uri of uris) {
        try {
          const [, elementType, elementId] = uri.split(":");
          const response = await fetch(
            `http://localhost:5000/open/${elementType}/${elementId}`,
            {
              method: "GET",
            }
          );

          if (!response.ok) {
            Spicetify.showNotification(
              "The song or album has not been downloaded yet !",
              false,
              3000
            );
          }
        } catch (error) {
          console.error(`Error opening file: ${error}`);
          Spicetify.showNotification(
            `${error}. Make sure the SpotifyDL server is running.`,
            true,
            3000
          );
          return;
        }
      }
    },
    (uris) => {
      if (!uris) return false;
      const validTypes = ["track", "album", "artist"];
      const isValidType = validTypes.some((type) =>
        uris[0].includes(`spotify:${type}:`)
      );
      if (!isValidType) return false;

      // Only enable button if all items are downloaded
      // Wait for all fetches to complete
      Promise.all(
        uris.map(async (uri) => {
          const [, elementType, elementId] = uri.split(":");
          try {
            const response = await fetch(
              `http://localhost:5000/is_downloaded/${elementType}/${elementId}`,
              {
                method: "GET",
              }
            );
            const isDownloaded = (await response.text()) === "true";
            return isDownloaded;
          } catch (error) {
            console.log(`${error}. The server is probably not running.`);
            return false;
          }
        })
      ).then((results) => {
        const allDownloaded = results.every((result) => result === true);
        openInExplorerButton.disabled = !allDownloaded;
      });

      return true;
    },
    "playlist-folder",
    false
  );

  downloadButton.register();
  openInExplorerButton.register();
  console.log("Download button loaded");
})();
