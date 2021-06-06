let form = document.getElementById("get-symbol");
let base = form.querySelector("#base");
let quote = form.querySelector("#quote");
let buy_perc = form.querySelector("#buy-perc");

form.addEventListener("submit", (event) => {
  event.preventDefault();
  fetch(
    "/addcoin?" +
      new URLSearchParams({
        base: base.value.toUpperCase(),
        quote: quote.value.toUpperCase(),
        percent: buy_perc.value,
      })
  );
});

let coin_list_refresh = document.getElementById("coin-list_refresh");
let coin_list = document.getElementById("coin-list");

coin_list.addEventListener("submit", (event) => {
  event.preventDefault();
  let formelm = event.target;
  fetch("/buycoin", {
    method: "POST",
    body: new FormData(formelm),
  });
});

coin_list_refresh.addEventListener("click", (event) => {
  fetch("/getcoins")
    .then((response) => {
      return response.json();
    })
    .then((response) => {
      coin_list.innerHTML = "";
      for (const coin in response) {
        let listitem = document.createElement("li");
        listitem.className = "list-item";
        let heading = document.createElement("p");
        heading.innerHTML = coin + " - " + response[coin];
        let base, quote;
        [base, quote] = coin.split(" ");
        let buy_form = document.createElement("form");

        let stop_tsl = document.createElement("button");
        stop_tsl.innerHTML = "stop tsl";
        stop_tsl.addEventListener("click", (event) => {
          fetch(
            "/stoptsl?" +
              new URLSearchParams({
                base: base,
                quote: quote,
              })
          );
        });

        let sell_all = document.createElement("button");
        sell_all.addEventListener("click", (event) => {
          fetch(
            "/sellall?" +
              new URLSearchParams({
                base: base,
                quote: quote,
              })
          );
        });

        sell_all.innerHTML = "sell all";

        let base_input = document.createElement("input");
        base_input.name = "base";
        base_input.value = base;
        let quote_input = document.createElement("input");
        quote_input.name = "quote";
        quote_input.value = quote;
        base_input.type = quote_input.type = "hidden";

        let buyelem = `<div>
            <label for="buy_percentage">Percentage (BUY)</label>
            <input id="but=y_percentage" name="buy_percentage" type="text" value="10"/>
            <div>
            `;
        let tsl = `<div>
            <label for="follow_percentage">TSL Follow percent</label>
            <input id="follow_percentage" name="follow_percentage" type="text" value="10"/>
            </div>
            <div>
            <label for="safety_percentage">TSL Safety percent</label>
            <input id="safety_percentage" name="safety_percentage" type="text" value="1"/>
            </div>
            `;
        let button = document.createElement("button");
        button.type = "submit";
        button.innerText = "Buy/TSL";
        let close_button = document.createElement("button");
        close_button.innerHTML = "remove";
        close_button.addEventListener("click", (event) => {
          fetch(
            "/removecoin?" +
              new URLSearchParams({
                base: base,
                quote: quote,
              })
          );
        });
        listitem.style.display = "flex";
        listitem.style.gap = '10px';
        let contain1 = document.createElement("section");
        let contain2 = document.createElement("section");
        
        contain2.innerHTML = `
        <form id="multi-limit">
          <input type="hidden" name="base" value="${base}"/>
          <input type="hidden" name="quote" value="${quote}"/>
          <div>
          <label for="sell-percent">Sell Percentages</label>
          <input id="sell-percent" type="text" name="sell-perc"/>
          </div>
          <div>
          <label for="sell-quantity">Sell Quantities</label>
          <input id="sell-quantitiy" type="text" name="sell-quant"/>
          </div>
          <button type="submit">Set Limits</button>
          </form>
        `
        let multi_form = contain2.querySelector('#multi-limit');
        multi_form.addEventListener('submit', event => {
          event.preventDefault();
          event.stopPropagation();
          fetch('/multilimit', {
            method: "POST",
            body: new FormData(multi_form),
          });  
        });

        buy_form.appendChild(heading);
        buy_form.appendChild(base_input);
        buy_form.appendChild(quote_input);
        buy_form.insertAdjacentHTML("beforeend", buyelem);
        buy_form.insertAdjacentHTML("beforeend", tsl);
        buy_form.appendChild(button);
        contain1.appendChild(buy_form);
        contain1.appendChild(stop_tsl);
        contain1.appendChild(sell_all);
        contain1.appendChild(close_button);
        listitem.appendChild(contain1);
        listitem.appendChild(contain2);
        coin_list.appendChild(listitem);
      }
    })
    .catch((error) => {
      console.log(error);
    });
});
